from __future__ import annotations

import json
import logging
import os
from datetime import date
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Tuple
from urllib.parse import urlencode

if TYPE_CHECKING:
    # Solo para anotaciones de tipo. En runtime Playwright se importa bajo demanda
    # (dependencia opcional del scraper, ver requirements-scraper.txt).
    from playwright.sync_api import Browser, BrowserContext, Page, Playwright

# Una sesión Playwright completa: playwright + browser + context + page.
BrowserSession = Tuple["Playwright", "Browser", "BrowserContext", "Page"]

from src.domain.model.courseModel import CourseModel
from src.domain.repository.sourceRepository import SourceRepository
from src.infraestructure.dto.emovies.emovieApiParamsDto import EmovieApiParamsDto
from src.infraestructure.dto.emovies.emovieApiResponseDto import (
    EmovieApiCourseDto,
    EmovieApiDataDto,
    EmovieApiResponseDto,
)
from src.infraestructure.dto.emovies.emovieswebScraperCourseDto import EmoviesWebScraperCourseDto
from src.infraestructure.mapper.emovies.emoviesMapper import emovieResponseToCourseModels, parseApiDatetime

logger = logging.getLogger("EmoviesSourceRepositoryImp")


class EmoviesSourceRepositoryImp(SourceRepository):
    """Fuente de cursos eMOVIES.

    eMOVIES protege admin-ajax.php con Imunify360 (reto JS). Un GET con
    requests recibe el HTML del challenge o un 403 de automatización.
    Playwright lanza Chromium, deja que el JS del challenge se resuelva y
    lee el JSON real.

    Imunify360 solo deja pasar la primera llamada admin-ajax de una sesión
    de navegador; las siguientes de la misma sesión se quedan atascadas en
    el challenge. Por eso cada página se consulta con una sesión Playwright
    nueva (creada y cerrada por página) y, si falla, se reintenta con otra
    sesión fresca. El número de reintentos se configura con el parámetro
    page_retries del constructor o con la variable de entorno
    EMOVIES_PAGE_RETRIES.
    """

    SOURCE_ID = 1  # id de la fuente en courses_sources (ver APP_COURSE_SOURCES en defaultValuesCatalog)
    API_URL = "https://emovies.oui-iohe.org/wp-admin/admin-ajax.php"
    SITE_URL = "https://emovies.oui-iohe.org/en/page-our-courses/"
    REQUEST_TIMEOUT_MS = 60_000
    CHALLENGE_TIMEOUT_MS = 60_000
    NO_FILTER_VALUE = "NaN"
    DEFAULT_PAGE_RETRIES = 2
    BROWSER_UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        web_scraper: Optional[Callable[[EmovieApiCourseDto], EmoviesWebScraperCourseDto]] = None,
        page_retries: Optional[int] = None,
    ):
        self._web_scraper = web_scraper
        self._page_retries = self._resolvePageRetries(page_retries)

    @staticmethod
    def _resolvePageRetries(page_retries: Optional[int]) -> int:
        """Resuelve los reintentos por página: parámetro explícito > env > default (2)."""
        if page_retries is None:
            envValue = os.getenv("EMOVIES_PAGE_RETRIES")
            if envValue:
                try:
                    page_retries = int(envValue)
                except ValueError:
                    logger.warning(
                        "EMOVIES_PAGE_RETRIES='%s' no es un entero válido; se usa el default %d",
                        envValue,
                        EmoviesSourceRepositoryImp.DEFAULT_PAGE_RETRIES,
                    )
                    page_retries = None
            if page_retries is None:
                page_retries = EmoviesSourceRepositoryImp.DEFAULT_PAGE_RETRIES
        return max(0, page_retries)

    def getCourses(self, max: Optional[int] = None) -> List[CourseModel]:
        apiParams = self._buildApiParams()
        pagesData = self._fetchAllCourses(apiParams, max)

        if pagesData is None:
            logger.warning("La API de eMOVIES no devolvió datos; se devuelve una lista vacía de cursos")
            return []

        coursesById: dict[int, EmovieApiCourseDto] = {}
        for pageData in pagesData:
            for courseDto in pageData.courses.posts or []:
                if courseDto.ID is not None:
                    coursesById[courseDto.ID] = courseDto

        logger.info("Se obtuvieron %d cursos únicos tras deduplicar por ID", len(coursesById))

        courseDtos = self._sortByDateDesc(list(coursesById.values()))

        # Se mapea cada página con su propio courses_html: los tags de área,
        # nivel e idioma quedan asociados a los cursos de esa misma página.
        # Antes se usaba el HTML de la página 1 junto con la lista global
        # reordenada, lo que dejaba sin áreas a casi todos los cursos y
        # desalineaba los primeros por el match posicional.
        modelsByCourseId: dict[int, CourseModel] = {}
        for pageData in pagesData:
            if pageData.courses is None or not (pageData.courses.posts or []):
                continue
            pageModels = emovieResponseToCourseModels(pageData, None)
            for courseModel, courseDto in zip(pageModels, pageData.courses.posts or []):
                if courseDto.ID is not None:
                    modelsByCourseId[courseDto.ID] = courseModel

        courseModels = [
            modelsByCourseId[courseDto.ID]
            for courseDto in courseDtos
            if courseDto.ID in modelsByCourseId
        ]
        courses: List[CourseModel] = list(courseModels)

        logger.info("getCourses devolvió %d cursos", len(courses))
        return courses

    def _buildApiParams(self) -> EmovieApiParamsDto:
        return EmovieApiParamsDto(
            uni_search="",
            course_levels=self.NO_FILTER_VALUE,
            uni_countries=self.NO_FILTER_VALUE,
            uni_languages=self.NO_FILTER_VALUE,
            course_university=self.NO_FILTER_VALUE,
            disciplinary_field=self.NO_FILTER_VALUE,
        )

    def _fetchAllCourses(
        self,
        apiParams: EmovieApiParamsDto,
        max: Optional[int] = None,
    ) -> Optional[List[EmovieApiDataDto]]:
        firstPageData = self._fetchPageWithRetry(apiParams, 1)
        if firstPageData is None:
            logger.warning(
                "No se pudo obtener la primera página de cursos de eMOVIES; se devolverá una lista vacía"
            )
            return None

        coursesPayload = firstPageData.courses
        maxtoMaxPages = max // 12 if max is not None else None
        maxNumPages = maxtoMaxPages or (coursesPayload.max_num_pages or firstPageData.max_num_page) or 1
        logger.info("La API de eMOVIES reporta %d páginas de cursos", maxNumPages)

        # La lista arranca con la primera página ya incluida; se consultan las restantes.
        pagesData: List[EmovieApiDataDto] = [firstPageData]
        for page in range(2, maxNumPages + 1):
            pageData = self._fetchPageWithRetry(apiParams, page)
            if pageData is None or pageData.courses is None:
                logger.warning(
                    "Página %d de eMOVIES sin datos tras %d intentos; se omite",
                    page,
                    self._page_retries + 1,
                )
                continue
            pagesData.append(pageData)

        logger.info("Se obtuvieron %d páginas de cursos desde eMOVIES", len(pagesData))
        return pagesData

    def _fetchPageWithRetry(
        self,
        apiParams: EmovieApiParamsDto,
        pageNumber: int,
    ) -> Optional[EmovieApiDataDto]:
        """Consulta una página con sesión fresca y reintenta con otra sesión nueva si falla.

        Cada intento crea su propio navegador: Imunify360 deja pasar la
        primera llamada admin-ajax de una sesión fresca y bloquea las
        siguientes de la misma sesión.
        """
        maxAttempts = self._page_retries + 1
        for attempt in range(1, maxAttempts + 1):
            try:
                pageData = self._fetchPageWithFreshBrowser(apiParams, pageNumber)
            except Exception as e:
                logger.warning(
                    "Intento %d de %d para la página %d de eMOVIES falló: %s",
                    attempt,
                    maxAttempts,
                    pageNumber,
                    str(e),
                )
                continue
            if pageData is not None:
                return pageData
            logger.warning(
                "Intento %d de %d para la página %d de eMOVIES sin datos",
                attempt,
                maxAttempts,
                pageNumber,
            )
        return None

    def _fetchPageWithFreshBrowser(
        self,
        apiParams: EmovieApiParamsDto,
        pageNumber: int,
    ) -> Optional[EmovieApiDataDto]:
        """Crea una sesión Playwright dedicada, consulta la página y la cierra."""
        playwright, browser, context, page = self._createBrowserSession()
        try:
            return self._fetchPageWithPage(page, apiParams, pageNumber)
        except Exception as e:
            logger.warning("La página %d de eMOVIES falló en su navegador: %s", pageNumber, str(e))
            return None
        finally:
            self._closeBrowserSession((playwright, browser, context, page))

    def _fetchPageWithPage(
        self,
        page: Page,
        apiParams: EmovieApiParamsDto,
        pageNumber: int,
    ) -> Optional[EmovieApiDataDto]:
        logger.info("Consultando página %d de la API de eMOVIES (Playwright)", pageNumber)
        pageParams = {**apiParams.model_dump(), "page": str(pageNumber)}

        try:
            payloadJson = self._getJsonViaBrowser(page, pageParams)
        except Exception as e:
            logger.warning(
                "No se pudo obtener la página %d de la API de eMOVIES vía Playwright: %s",
                pageNumber,
                str(e),
            )
            return None

        try:
            payload = EmovieApiResponseDto.model_validate(payloadJson)
        except Exception as e:
            logger.error(
                "Error al parsear la respuesta JSON de la API de eMOVIES en la página %d: %s",
                pageNumber,
                str(e),
            )
            return None

        if not payload.success:
            logger.warning("La API de eMOVIES respondió success=false en la página %d", pageNumber)
            return None

        if payload.data is None or payload.data.courses is None:
            logger.warning("La API de eMOVIES no devolvió cursos en la página %d", pageNumber)
            return None

        logger.info("Página %d devolvió %d cursos", pageNumber, len(payload.data.courses.posts or []))
        return payload.data

    def _createBrowserSession(self) -> BrowserSession:
        """Crea una sesión Playwright completa: playwright + browser + context + page.

        Incluye la visita previa al sitio (cookies de primera parte + Referer
        creíble).
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise RuntimeError(
                "Playwright no está instalado. Instala las dependencias del scraper: "
                "pip install -r requirements-scraper.txt y luego: playwright install chromium"
            ) from e

        logger.info("Iniciando Chromium (Playwright) para eMOVIES")
        playwright = sync_playwright().start()
        try:
            browser = playwright.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
        except Exception as e:
            playwright.stop()
            raise RuntimeError(
                "No se pudo lanzar Chromium de Playwright. "
                "Instálalo con: playwright install chromium"
            ) from e
        context = browser.new_context(
            user_agent=self.BROWSER_UA,
            locale="es-ES",
            viewport={"width": 1365, "height": 900},
            java_script_enabled=True,
        )
        # Reduce la huella de automatización que Imunify360 detecta (navigator.webdriver).
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        page = context.new_page()
        page.set_default_timeout(self.REQUEST_TIMEOUT_MS)

        # Visita previa al sitio: cookies de primera parte + Referer creíble.
        try:
            page.goto(self.SITE_URL, wait_until="domcontentloaded", timeout=self.REQUEST_TIMEOUT_MS)
        except Exception as e:
            logger.warning("No se pudo precargar la página de cursos eMOVIES: %s", str(e))

        return playwright, browser, context, page

    def _closeBrowserSession(self, session: BrowserSession) -> None:
        playwright, browser, context, page = session
        for closer, label in (
            (page, "page"),
            (context, "context"),
            (browser, "browser"),
        ):
            if closer is None:
                continue
            try:
                closer.close()
            except Exception as e:
                logger.debug("Error al cerrar %s de Playwright: %s", label, str(e))

        if playwright is not None:
            try:
                playwright.stop()
            except Exception as e:
                logger.debug("Error al detener Playwright: %s", str(e))

    def _getJsonViaBrowser(self, page: Page, params: dict[str, Any]) -> Any:
        if page is None:
            raise RuntimeError("El browser de Playwright no está iniciado")

        url = f"{self.API_URL}?{urlencode(params)}"
        logger.debug("Playwright GET %s", url)
        page.goto(url, wait_until="domcontentloaded", timeout=self.REQUEST_TIMEOUT_MS)
        self._waitForJsonBody(page)
        text = page.evaluate("() => (document.body && document.body.innerText) || ''")
        text = (text or "").strip()
        if not text:
            raise RuntimeError("La página de eMOVIES devolvió cuerpo vacío tras el challenge")

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            preview = text[:200].replace("\n", " ")
            raise RuntimeError(
                f"La respuesta de eMOVIES no es JSON válido tras el challenge: {preview!r}"
            ) from e

    def _waitForJsonBody(self, page: Page) -> None:
        """Espera a que el challenge de Imunify360 termine y el body sea JSON."""
        page.wait_for_function(
            """() => {
                const t = ((document.body && document.body.innerText) || '').trim();
                if (!t) return false;
                if (t.startsWith('{') || t.startsWith('[')) return true;
                // 403 explícito de Imunify360 también es JSON usable para diagnosticar.
                if (t.includes('Access denied by Imunify360')) return true;
                return false;
            }""",
            timeout=self.CHALLENGE_TIMEOUT_MS,
        )

    def _sortByDateDesc(self, courseDtos: List[EmovieApiCourseDto]) -> List[EmovieApiCourseDto]:
        sortedDtos = sorted(
            courseDtos,
            key=lambda courseDto: self._courseDate(courseDto),
            reverse=True,
        )
        logger.debug("Cursos ordenados por fecha descendente: %d", len(sortedDtos))
        return sortedDtos

    def _courseDate(self, courseDto: EmovieApiCourseDto) -> date:
        parsedDates = [
            parsedDate
            for parsedDate in (
                parseApiDatetime(courseDto.post_date),
                parseApiDatetime(courseDto.post_modified),
            )
            if parsedDate is not None
        ]

        if not parsedDates:
            return date.min

        return max(parsedDates)

    def _scrapeCourseDetail(self, courseDto: EmovieApiCourseDto) -> EmoviesWebScraperCourseDto:
        """Hook para el futuro scraper web.

        Hasta que exista, devuelve un DTO vacío y el mapper usa valores por defecto.
        """
        if self._web_scraper is None:
            logger.debug(
                "Scraper web no configurado; se usarán valores por defecto para el curso %s",
                courseDto.ID,
            )
            return EmoviesWebScraperCourseDto()

        logger.debug("Scrapeando detalle web del curso %s", courseDto.ID)
        return self._web_scraper(courseDto)
