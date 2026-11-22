import re

from app.services.media import (
    IMAGES_SUBDIR,
    MAX_RASTER_BYTES,
    MAX_SVG_BYTES,
    MEDIA_DIR,
    prepare_image,
)

IMAGE_URL_RE = re.compile(
    r"^/media/images/" r"[A-Za-z0-9_-][A-Za-z0-9_.-]*" r"\.(?:jpg|jpeg|png|webp|svg)$",
    re.IGNORECASE,
)

LEGACY_LINK_RE = re.compile(
    r"^\[([^\]\r\n]+)\]" r"\(\s*(/media/images/[^)\r\n]+)\s*\)$"
)


def validate_image_url(url: str) -> None:
    """Проверяет URL, наличие файла и его формат."""
    if not IMAGE_URL_RE.fullmatch(url):
        raise ValueError("Выберите изображение из медиатеки: JPG, PNG, WebP или SVG.")

    root = (MEDIA_DIR / IMAGES_SUBDIR).resolve()
    filename = url.rsplit("/", 1)[-1]
    path = (root / filename).resolve()

    if path.parent != root or not path.is_file():
        raise ValueError("Файл изображения отсутствует на сервере.")

    limit = max(MAX_RASTER_BYTES, MAX_SVG_BYTES)

    if path.stat().st_size > limit:
        raise ValueError("Файл изображения превышает допустимый размер.")

    extension, _ = prepare_image(path.read_bytes())

    suffix = path.suffix.lower()
    if suffix == ".jpeg":
        suffix = ".jpg"

    if suffix != extension:
        raise ValueError("Расширение изображения не соответствует содержимому.")


def validate_specification_value(
    value_type: str,
    value: str | None,
    asset_id: int | None,
    image_url: str | None = None,
) -> str:
    """Возвращает нормализованное значение либо вызывает ValueError."""
    if value_type not in ("text", "image"):
        raise ValueError("Неизвестный тип значения характеристики.")

    text = (value or "").strip()

    if not text:
        raise ValueError("Введите значение характеристики или подпись изображения.")

    if len(text) > 500:
        raise ValueError("Значение характеристики не должно превышать 500 символов.")

    if re.fullmatch(
        r"\[[^\]\r\n]+\]\([^\r\n]*\)",
        text,
    ):
        raise ValueError(
            "Не вводите Markdown-ссылку. "
            "Выберите тип «Изображение», "
            "введите подпись и выберите файл отдельно."
        )

    if value_type == "text":
        if asset_id is not None:
            raise ValueError("Для типа «Текст» очистите поле изображения.")

    if value_type == "image":
        if asset_id is None or not image_url:
            raise ValueError("Для типа «Изображение» выберите файл из медиатеки.")

        validate_image_url(image_url)

    return text
