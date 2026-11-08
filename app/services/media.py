"""
app/services/media.py
Загрузка и проверка изображений товаров для админки.

Файлы сохраняются в media/products/ под случайным именем, в базе хранится
путь вида /media/products/<uuid>.<ext>. Имя файла от пользователя не используется.
"""

import re
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import anyio

# Та же папка, что монтируется как /media в app/main.py
MEDIA_DIR = Path(__file__).resolve().parents[2] / "media"
PRODUCTS_SUBDIR = "products"
PRODUCTS_URL_PREFIX = f"/media/{PRODUCTS_SUBDIR}/"

MAX_RASTER_BYTES = 5 * 1024 * 1024
MAX_SVG_BYTES = 512 * 1024

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

ALLOWED_SVG_TAGS = {
    "svg",
    "g",
    "defs",
    "title",
    "desc",
    "path",
    "line",
    "polyline",
    "polygon",
    "rect",
    "circle",
    "ellipse",
    "text",
    "tspan",
    "marker",
    "use",
    "symbol",
    "clipPath",
    "mask",
    "linearGradient",
    "radialGradient",
    "stop",
    "pattern",
}

ALLOWED_SVG_ATTRS = {
    "id",
    "class",
    "viewBox",
    "width",
    "height",
    "x",
    "y",
    "x1",
    "y1",
    "x2",
    "y2",
    "cx",
    "cy",
    "r",
    "rx",
    "ry",
    "d",
    "points",
    "transform",
    "fill",
    "stroke",
    "stroke-width",
    "stroke-dasharray",
    "stroke-dashoffset",
    "stroke-linecap",
    "stroke-linejoin",
    "stroke-miterlimit",
    "fill-opacity",
    "stroke-opacity",
    "opacity",
    "fill-rule",
    "clip-rule",
    "font-family",
    "font-size",
    "font-style",
    "font-weight",
    "text-anchor",
    "dominant-baseline",
    "letter-spacing",
    "dx",
    "dy",
    "rotate",
    "marker-start",
    "marker-mid",
    "marker-end",
    "markerWidth",
    "markerHeight",
    "markerUnits",
    "refX",
    "refY",
    "orient",
    "preserveAspectRatio",
    "version",
    "offset",
    "stop-color",
    "stop-opacity",
    "gradientUnits",
    "gradientTransform",
    "patternUnits",
    "patternTransform",
    "clip-path",
    "mask",
    "clipPathUnits",
    "maskUnits",
    "href",
}

_SAFE_URL_REF = re.compile(r"^url\(\s*#[\w.\-:]+\s*\)$")
_URL_IN_VALUE = re.compile(r"url\(", re.IGNORECASE)
_DANGEROUS_VALUE = re.compile(
    r"javascript:|data:|expression\(|@import|<|>", re.IGNORECASE
)


class MediaValidationError(ValueError):
    """Файл не прошёл проверку; текст ошибки показывается в админке."""


def _local(name: str) -> tuple[str, str]:
    """'{ns}tag' -> (ns, 'tag')"""
    if name.startswith("{"):
        ns, _, local = name[1:].partition("}")
        return ns, local
    return "", name


def _attr_is_safe(name: str, value: str) -> bool:
    ns, local = _local(name)
    if ns == XLINK_NS and local == "href":
        return value.startswith("#")
    if ns:
        return False
    if local not in ALLOWED_SVG_ATTRS:
        return False
    if local == "href":
        return value.startswith("#")
    if _URL_IN_VALUE.search(value) and not _SAFE_URL_REF.match(value.strip()):
        return False
    return not _DANGEROUS_VALUE.search(value)


def _sanitize_element(element: ET.Element) -> None:
    for child in list(element):
        ns, local = _local(child.tag)
        if ns != SVG_NS or local not in ALLOWED_SVG_TAGS:
            element.remove(child)
            continue
        _sanitize_element(child)

    for name in list(element.attrib):
        if not _attr_is_safe(name, element.attrib[name]):
            del element.attrib[name]


def sanitize_svg(content: bytes) -> bytes:
    """Оставляет в SVG только безопасные элементы и атрибуты."""
    if len(content) > MAX_SVG_BYTES:
        raise MediaValidationError("SVG слишком большой (максимум 512 КБ).")

    lowered = content.lower()
    if b"<!doctype" in lowered or b"<!entity" in lowered:
        raise MediaValidationError("SVG с DOCTYPE и ENTITY не принимается.")

    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise MediaValidationError("Некорректный SVG-файл.") from exc

    ns, local = _local(root.tag)
    if ns != SVG_NS or local != "svg":
        raise MediaValidationError("Файл не является SVG-изображением.")

    _sanitize_element(root)

    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", XLINK_NS)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def detect_raster_extension(content: bytes) -> str | None:
    """Определяет формат по сигнатуре файла, а не по имени."""
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ".webp"
    return None


def prepare_image(content: bytes) -> tuple[str, bytes]:
    """Возвращает (расширение, безопасное содержимое) или бросает MediaValidationError."""
    if not content:
        raise MediaValidationError("Файл пустой.")

    extension = detect_raster_extension(content)
    if extension:
        if len(content) > MAX_RASTER_BYTES:
            raise MediaValidationError("Изображение слишком большое (максимум 5 МБ).")
        return extension, content

    head = content[:2048].lstrip(b"\xef\xbb\xbf \t\r\n").lower()
    if head.startswith(b"<?xml") or head.startswith(b"<svg"):
        return ".svg", sanitize_svg(content)

    raise MediaValidationError("Допустимы файлы JPG, PNG, WebP и SVG.")


async def save_product_image(upload: Any) -> str:
    """Принимает UploadFile, сохраняет файл и возвращает путь для image_url."""
    limit = max(MAX_RASTER_BYTES, MAX_SVG_BYTES) + 1
    content = await upload.read(limit)
    extension, safe_content = prepare_image(content)

    target_dir = MEDIA_DIR / PRODUCTS_SUBDIR
    name = f"{uuid.uuid4().hex}{extension}"
    target = target_dir / name

    def write() -> None:
        target_dir.mkdir(parents=True, exist_ok=True)
        target.write_bytes(safe_content)

    await anyio.to_thread.run_sync(write)
    return f"{PRODUCTS_URL_PREFIX}{name}"


def delete_product_image_file(image_url: str | None) -> None:
    """Удаляет файл, загруженный через админку. Чужие и внешние адреса не трогает."""
    if not image_url or not image_url.startswith(PRODUCTS_URL_PREFIX):
        return

    name = image_url[len(PRODUCTS_URL_PREFIX) :]
    if not name or "/" in name or "\\" in name or name.startswith("."):
        return

    path = (MEDIA_DIR / PRODUCTS_SUBDIR / name).resolve()
    if path.parent != (MEDIA_DIR / PRODUCTS_SUBDIR).resolve():
        return
    path.unlink(missing_ok=True)
