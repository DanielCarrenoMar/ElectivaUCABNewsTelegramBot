from __future__ import annotations

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
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
from src.domain.repository.courseRepository import CourseFilters, CourseSourceRepository
from src.infraestructure.dto.emovies.emovieApiParamsDto import EmovieApiParamsDto
from src.infraestructure.dto.emovies.emovieApiResponseDto import (
    EmovieApiCourseDto,
    EmovieApiCoursesDto,
    EmovieApiDataDto,
    EmovieApiResponseDto,
)
from src.infraestructure.dto.emovies.emovieswebScraperCourseDto import EmoviesWebScraperCourseDto
from src.infraestructure.mapper.emovies.emoviesMapper import emovieResponseToCourseModels, parseApiDatetime

logger = logging.getLogger("EmoviesSourceRepositoryImp")


class EmoviesSourceRepositoryImp(CourseSourceRepository):
    """Fuente de cursos eMOVIES.

    eMOVIES protege admin-ajax.php con Imunify360 (reto JS). Un GET con
    requests recibe el HTML del challenge o un 403 de automatización.
    Playwright lanza Chromium, deja que el JS del challenge se resuelva y
    lee el JSON real.

    Con browser_count > 1 las páginas de la API se consultan en paralelo:
    cada worker usa un navegador dedicado (la sync API de Playwright no es
    thread-safe, así que cada thread crea su propia sesión). El número de
    navegadores se configura con el parámetro browser_count del constructor
    o con la variable de entorno EMOVIES_BROWSER_COUNT; con 1 el
    comportamiento es el original (una sesión reutilizada, secuencial).
    """

    API_URL = "https://emovies.oui-iohe.org/wp-admin/admin-ajax.php"
    SITE_URL = "https://emovies.oui-iohe.org/en/page-our-courses/"
    REQUEST_TIMEOUT_MS = 60_000
    CHALLENGE_TIMEOUT_MS = 60_000
    NO_FILTER_VALUE = "NaN"
    BROWSER_UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        web_scraper: Optional[Callable[[EmovieApiCourseDto], EmoviesWebScraperCourseDto]] = None,
        browser_count: Optional[int] = None,
    ):
        self._web_scraper = web_scraper
        self._browser_count = self._resolveBrowserCount(browser_count)
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    @staticmethod
    def _resolveBrowserCount(browser_count: Optional[int]) -> int:
        """Resuelve el número de navegadores: parámetro explícito > env > default (1)."""
        if browser_count is None:
            envValue = os.getenv("EMOVIES_BROWSER_COUNT")
            if envValue:
                try:
                    browser_count = int(envValue)
                except ValueError:
                    logger.warning(
                        "EMOVIES_BROWSER_COUNT='%s' no es un entero válido; se usa el default %d",
                        envValue,
                        EmoviesSourceRepositoryImp.DEFAULT_BROWSER_COUNT,
                    )
                    browser_count = None
            if browser_count is None:
                browser_count = EmoviesSourceRepositoryImp.DEFAULT_BROWSER_COUNT
        return max(1, browser_count)

    def getCourses(self, filters: CourseFilters, max: Optional[int] = None) -> List[CourseModel]:
        apiParams = self._buildApiParams(filters)
        if self._browser_count > 1:
            pagesData = self._fetchAllCoursesParallel(apiParams, max)
        else:
            try:
                self._startBrowser()
                pagesData = self._fetchAllCourses(apiParams, max)
            finally:
                self._stopBrowser()

        if pagesData is None:
            logger.warning("La API de eMOVIES no devolvió datos; se devuelve una lista vacía de cursos")
            return []

        coursesById: dict[int, EmovieApiCourseDto] = {}
        for pageData in pagesData:
            for courseDto in pageData.courses.posts or []:
                if courseDto.ID is not None:
                    coursesById[courseDto.ID] = courseDto

        logger.info("Se obtuvieron %d cursos únicos tras deduplicar por ID", len(coursesById))

        courseDtos = self._filterByMinModifiedDate(list(coursesById.values()), filters.minModifiedDate)
        courseDtos = self._sortByDateDesc(courseDtos)

        firstPageDataDto = pagesData[0]
        mappedData = firstPageDataDto.model_copy(update={"courses": EmovieApiCoursesDto(posts=courseDtos)})
        courseModels = emovieResponseToCourseModels(mappedData, None)
        courses: List[CourseModel] = []

        for courseModel in courseModels:
            if filters.minStudyHours is not None and courseModel.studyHours < filters.minStudyHours:
                logger.debug(
                    "Curso '%s' descartado: studyHours %d < minStudyHours %d",
                    courseModel.title,
                    courseModel.studyHours,
                    filters.minStudyHours,
                )
                continue
            courses.append(courseModel)

        logger.info("getCourses devolvió %d cursos", len(courses))
        return courses

    def _buildApiParams(self, filters: CourseFilters) -> EmovieApiParamsDto:
        return EmovieApiParamsDto(
            uni_search=filters.keyword or "",
            course_levels=filters.courseLevel or self.NO_FILTER_VALUE,
            uni_countries=filters.country or self.NO_FILTER_VALUE,
            uni_languages=filters.language or self.NO_FILTER_VALUE,
            course_university=filters.university or self.NO_FILTER_VALUE,
            disciplinary_field=filters.disciplinaryField or self.NO_FILTER_VALUE,
        )

    def _fetchAllCourses(
        self,
        apiParams: EmovieApiParamsDto,
        max: Optional[int] = None,
    ) -> Optional[List[EmovieApiDataDto]]:
        firstPageData = self._fetchPage(apiParams, 1)
        if firstPageData is None:
            logger.warning(
                "No se pudo obtener la primera página de cursos de eMOVIES; se devolverá una lista vacía"
            )
            return None

        coursesPayload = firstPageData.courses
        maxNumPages = max // 12 or (coursesPayload.max_num_pages or firstPageData.max_num_page) or 1
        logger.info("La API de eMOVIES reporta %d páginas de cursos", maxNumPages)

        # La lista arranca con la primera página ya incluida; se consultan las restantes.
        pagesData: List[EmovieApiDataDto] = [firstPageData]
        for page in range(2, maxNumPages + 1):
            pageData = self._fetchPage(apiParams, page)
            if pageData is None or pageData.courses is None:
                logger.warning("Página %d de eMOVIES sin datos; se omite", page)
                continue
            pagesData.append(pageData)

        logger.info("Se obtuvieron %d páginas de cursos desde eMOVIES", len(pagesData))
        return pagesData

    def _fetchAllCoursesParallel(
        self,
        apiParams: EmovieApiParamsDto,
        max: Optional[int] = None,
    ) -> Optional[List[EmovieApiDataDto]]:
        """Obtiene todas las páginas con hasta browser_count navegadores en paralelo.

        La primera página se resuelve en el pool (necesaria para conocer el
        número total de páginas) y las restantes se reparten entre los
        workers, cada uno con su propio navegador dedicado. El orden de la
        lista final no importa: getCourses deduplica y ordena por fecha, y la
        página 1 queda siempre en la posición 0.
        """
        maxWorkers = self._browser_count
        logger.info("Obteniendo cursos de eMOVIES con %d navegadores en paralelo", maxWorkers)

        with ThreadPoolExecutor(max_workers=maxWorkers, thread_name_prefix="emovies-browser") as executor:
            firstFuture = executor.submit(self._fetchPageWithOwnBrowser, apiParams, 1)
            firstPageData = firstFuture.result()
            if firstPageData is None:
                logger.warning(
                    "No se pudo obtener la primera página de cursos de eMOVIES; se devolverá una lista vacía"
                )
                return None

            coursesPayload = firstPageData.courses
            maxNumPages = (coursesPayload.max_num_pages or firstPageData.max_num_page) or 1
            logger.info("La API de eMOVIES reporta %d páginas de cursos", maxNumPages)

            # La lista arranca con la primera página ya incluida; las restantes se reparten en paralelo.
            pagesData: List[EmovieApiDataDto] = [firstPageData]
            pendingFutures = {
                executor.submit(self._fetchPageWithOwnBrowser, apiParams, page): page
                for page in range(2, maxNumPages + 1)
            }
            for future in as_completed(pendingFutures):
                page = pendingFutures[future]
                try:
                    pageData = future.result()
                except Exception as e:
                    logger.warning("Página %d de eMOVIES falló en su worker: %s", page, str(e))
                    continue
                if pageData is None or pageData.courses is None:
                    logger.warning("Página %d de eMOVIES sin datos; se omite", page)
                    continue
                pagesData.append(pageData)

        logger.info("Se obtuvieron %d páginas de cursos desde eMOVIES", len(pagesData))
        return pagesData

    def _fetchPage(self, apiParams: EmovieApiParamsDto, page: int) -> Optional[EmovieApiDataDto]:
        """Consulta una página con la sesión de navegador compartida (modo secuencial)."""
        if self._page is None:
            raise RuntimeError("El browser de Playwright no está iniciado")
        return self._fetchPageWithPage(self._page, apiParams, page)

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

    def _startBrowser(self) -> None:
        if self._page is not None:
            return
        self._playwright, self._browser, self._context, self._page = self._createBrowserSession()

    def _stopBrowser(self) -> None:
        self._closeBrowserSession((self._playwright, self._browser, self._context, self._page))
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None

    def _createBrowserSession(self) -> BrowserSession:
        """Crea una sesión Playwright completa: playwright + browser + context + page.

        Incluye la visita previa al sitio (cookies de primera parte + Referer
        creíble). La sync API de Playwright no es thread-safe: en modo paralelo
        cada worker crea su propia sesión dentro de su propio thread.
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

    def _fetchPageWithOwnBrowser(
        self,
        apiParams: EmovieApiParamsDto,
        pageNumber: int,
    ) -> Optional[EmovieApiDataDto]:
        """Worker paralelo: crea un navegador dedicado, consulta la página y lo cierra."""
        playwright, browser, context, page = self._createBrowserSession()
        try:
            return self._fetchPageWithPage(page, apiParams, pageNumber)
        except Exception as e:
            logger.warning("Worker de la página %d de eMOVIES falló: %s", pageNumber, str(e))
            return None
        finally:
            self._closeBrowserSession((playwright, browser, context, page))

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

    def _filterByMinModifiedDate(
        self,
        courseDtos: List[EmovieApiCourseDto],
        minModifiedDate: Optional[date],
    ) -> List[EmovieApiCourseDto]:
        if minModifiedDate is None:
            return courseDtos

        filtered: List[EmovieApiCourseDto] = []
        for courseDto in courseDtos:
            modifiedDate = parseApiDatetime(courseDto.post_modified)
            if modifiedDate is not None and modifiedDate >= minModifiedDate:
                filtered.append(courseDto)

        logger.info(
            "Filtro por fecha mínima %s: %d cursos -> %d cursos",
            minModifiedDate,
            len(courseDtos),
            len(filtered),
        )
        return filtered

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
