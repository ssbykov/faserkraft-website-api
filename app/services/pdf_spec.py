import logging
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.schemas.company import CompanyOut
from app.schemas.schemas import ProductOut

logger = logging.getLogger(__name__)

# app/services/pdf_spec.py -> корень проекта
PROJECT_DIR = Path(__file__).resolve().parents[2]

TEMPLATES_DIR = PROJECT_DIR / "app" / "templates"
MEDIA_DIR = PROJECT_DIR / "media"

_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def media_file_uri(image_url: str | None) -> str | None:
    """Преобразует URL /media/... в URI существующего локального файла."""
    if not image_url:
        return None

    # В этой реализации используются только локальные URL /media/...
    parsed = urlsplit(image_url.strip())
    if parsed.scheme or parsed.netloc:
        logger.warning(
            "PDF: ожидается локальный URL изображения /media/...: %s",
            image_url,
        )
        return None

    path = unquote(parsed.path)
    if not path.startswith("/media/"):
        return None

    media_root = MEDIA_DIR.resolve()
    file_path = (media_root / path.removeprefix("/media/")).resolve()

    # Не разрешаем выход за пределы каталога media.
    if not file_path.is_relative_to(media_root):
        logger.warning("PDF: недопустимый путь изображения: %s", image_url)
        return None

    if not file_path.is_file():
        logger.warning("PDF: файл изображения не найден: %s", file_path)
        return None

    return file_path.as_uri()


def render_product_spec_pdf(
    product: ProductOut, company: CompanyOut | None = None
) -> bytes:
    sorted_specs = sorted(
        product.specifications or [],
        key=lambda spec: spec.sort_order,
    )

    grouped: dict[str, list] = defaultdict(list)

    for spec in sorted_specs:
        group_name = (spec.group_name or "").strip() or "Основные характеристики"
        grouped[group_name].append(spec)

    images = sorted(
        product.images or [],
        key=lambda image: (image.sort_order, image.id),
    )

    drawings: list[dict[str, str]] = []

    for image in images:
        src = media_file_uri(image.image_url)
        if src is None:
            continue

        drawings.append(
            {
                "src": src,
                "title": ((image.alt_text or "").strip() or product.name),
            }
        )

    template = _jinja_env.get_template("product_spec.html")
    html_str = template.render(
        product=product,
        grouped_specs=grouped,
        drawings=drawings,
        company=company,
    )

    return HTML(
        string=html_str,
        base_url=TEMPLATES_DIR.as_uri() + "/",
    ).write_pdf()
