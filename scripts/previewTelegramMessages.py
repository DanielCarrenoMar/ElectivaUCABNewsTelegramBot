"""Imprime en la terminal el mensaje tal como lo recibiría un chat de Telegram.

Es una herramienta de prueba: no envía nada y no escribe en ninguna base. Usa el
mismo camino que el envío real (`courseRecordToShowCourseModel` y
`ShowCourseModel.buildMessage`), así que el HTML que se imprime es exactamente el
que se manda por Telegram.

La fecha que recibe es el día de la última revisión de un chat: se muestran
los cursos con `courses.created_at` estrictamente posterior a ese día a las 00:00
(GMT), la misma comparación que hace `chatconfigs.lastrevision`. Igual que el
envío real, el script no aplica los filtros de ningún chat.

Uso:
    python scripts/previewTelegramMessages.py 2026-10-01
    python scripts/previewTelegramMessages.py 01/10/2026 --plain --limit 5
"""

import argparse
import logging
import os
import pathlib
import re
import sys
from datetime import datetime

from dotenv import load_dotenv

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src.domain.model.courseModel import ShowCourseModel
from src.infraestructure.mapper.courseRecordMapper import courseRecordToShowCourseModel
from src.infraestructure.repositoryImp.coursesRepositoryImp import CoursesRepositoryImp

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(name)s.%(funcName)s: %(message)s",
    force=True,
)

DEFAULT_LIMIT = 20
SEPARATOR = "=" * 78

# Sin esto el enlace se perdería al quitar el HTML: primero el ancla queda como
# "título (url)" y después se eliminan las etiquetas que sobran.
_ANCHOR = re.compile(r'<a href="([^"]*)"[^>]*>(.*?)</a>', re.DOTALL)
_TAG = re.compile(r"<[^>]+>")


def parseDay(value: str) -> datetime:
    """Día de la última actualización, como YYYY-MM-DD o DD/MM/YYYY, a las 00:00."""
    for dayFormat in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value.strip(), dayFormat)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"fecha inválida '{value}': se espera YYYY-MM-DD o DD/MM/YYYY"
    )


def plainText(message: str) -> str:
    """Versión sin HTML del mensaje, con el enlace visible junto al título."""
    withLinks = _ANCHOR.sub(lambda match: f"{match.group(2)} ({match.group(1)})", message)
    return _TAG.sub("", withLinks)


def renderMessage(course: ShowCourseModel, plain: bool) -> str:
    """El texto que se envía por Telegram: tal cual, o sin HTML si plain es True."""
    message = course.buildMessage()
    return plainText(message) if plain else message


def previewTelegramMessages(since: datetime, plain: bool, limit: int) -> int:
    load_dotenv()

    if not os.getenv("COURSES_DB_URL"):
        raise RuntimeError("Falta variable de entorno COURSES_DB_URL")

    coursesRepository = CoursesRepositoryImp()
    records = coursesRepository.getCoursesCreatedAfter(since)
    print(
        f"Simulando un chat con lastrevision = {since.isoformat(sep=' ')} GMT: "
        f"{len(records)} curso(s) creado(s) después de esa fecha"
    )
    if not records:
        return 0

    # --limit 0 es "todos": el recorte se avisa, nunca se hace en silencio.
    shown = records if limit <= 0 else records[:limit]
    if len(shown) < len(records):
        print(f"Mostrando {len(shown)} de {len(records)} (--limit 0 para verlos todos)")
    if plain:
        print("Modo --plain: HTML quitado, el enlace se muestra junto al título")

    areasByCourse = coursesRepository.getKnowledgeAreasByCourseIds(
        [record.id for record in shown]
    )
    for position, record in enumerate(shown, start=1):
        course = courseRecordToShowCourseModel(record, areasByCourse.get(record.id, []))
        print(SEPARATOR)
        print(f"Curso {position}/{len(shown)} — id {record.id} — creado {record.createdAt}")
        print(SEPARATOR)
        print(renderMessage(course, plain))

    print(SEPARATOR)
    return len(records)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Imprime en la terminal el mensaje que se enviaría por Telegram para los "
            "cursos actualizados después de un día. No envía nada."
        )
    )
    parser.add_argument(
        "fecha",
        type=parseDay,
        help=(
            "Día de la última actualización (YYYY-MM-DD o DD/MM/YYYY): se muestran los "
            "cursos actualizados después de ese día a las 00:00 GMT."
        ),
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Quita el HTML para leerlo en la terminal; el enlace queda junto al título.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Máximo de cursos a imprimir (default {DEFAULT_LIMIT}; 0 = todos).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Muestra los logs de las consultas al catálogo.",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    previewTelegramMessages(args.fecha, args.plain, args.limit)
    return 0


if __name__ == "__main__":
    # La consola de Windows no es UTF-8 por defecto y los mensajes traen emojis:
    # sin esto imprimirlos lanzaría UnicodeEncodeError.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
