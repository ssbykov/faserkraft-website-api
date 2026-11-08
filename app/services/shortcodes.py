"""
Шорткоды медиа-библиотеки в HTML страниц и описаний товаров.

Синтаксис в тексте:
    {{media:12}}
    {{media:12 caption="Типоразмер 1"}}
    {{media:12 alt="Габаритный чертёж" zoom="0"}}

Сервер заменяет шорткод на <figure> с изображением из media_assets. По умолчанию
изображение открывается в модальном окне (атрибут data-drawing-preview).
Шорткод лучше ставить отдельной строкой, а не внутри абзаца.
"""

import html as html_lib
import logging
import re
from typing import Any, Awaitable, Callable, Iterable, Mapping, Protocol

logger = logging.getLogger(__name__)


class MediaAssetLike(Protocol):
    id: int
    file_url: str
    title: str | None
    alt_text: str | None


AssetLoader = Callable[[set[int]], Awaitable[Mapping[int, Any]]]

_QUOTES = '"\u201c\u201d'
_ATTR = rf'\s+\w+\s*=\s*[{_QUOTES}][^{_QUOTES}]*[{_QUOTES}]'
SHORTCODE_RE = re.compile(
    rf"\{{\{{\s*media\s*:\s*(?P<id>\d+)(?P<attrs>(?:{_ATTR})*)\s*\}}\}}"
)
ATTR_RE = re.compile(rf'(?P<name>\w+)\s*=\s*[{_QUOTES}](?P<value>[^{_QUOTES}]*)[{_QUOTES}]')
# Абзац, в котором есть только шорткод: <figure> внутри <p> недопустим
WRAPPED_RE = re.compile(
    rf"<p[^>]*>\s*(?P<code>{SHORTCODE_RE.pattern})\s*</p>", re.IGNORECASE
)

SAFE_URL_RE = re.compile(r"^(/|https?://)", re.IGNORECASE)
FALSY = {"0", "false", "no", "off", "нет"}
MAX_SHORTCODES = 100


def find_media_ids(content: str | None) -> set[int]:
    """Номера файлов, упомянутые в шорткодах."""
    if not content:
        return set()
    ids = {int(m.group("id")) for m in SHORTCODE_RE.finditer(content)}
    return set(sorted(ids)[:MAX_SHORTCODES])


def _escape(value: str) -> str:
    return html_lib.escape(value, quote=True)


def _parse_attrs(raw: str) -> dict[str, str]:
    return {
        m.group("name").lower(): m.group("value").strip()
        for m in ATTR_RE.finditer(raw or "")
    }


def _render_figure(asset: Any, attrs: dict[str, str]) -> str:
    url = (asset.file_url or "").strip()
    if not SAFE_URL_RE.match(url):
        return ""

    caption = attrs.get("caption", "")
    alt = attrs.get("alt") or asset.alt_text or caption or asset.title or ""
    title = caption or attrs.get("alt") or asset.alt_text or asset.title or ""
    zoom = attrs.get("zoom", "1").lower() not in FALSY

    image = (
        f'<img src="{_escape(url)}" alt="{_escape(alt)}" '
        f'loading="lazy" decoding="async">'
    )
    if zoom:
        image = (
            f'<a href="{_escape(url)}" class="media-figure__link" '
            f'data-drawing-preview data-drawing-title="{_escape(title)}" '
            f'aria-haspopup="dialog" aria-controls="drawing-dialog" '
            f'aria-label="Увеличить изображение">{image}</a>'
        )

    figcaption = f"<figcaption>{_escape(caption)}</figcaption>" if caption else ""
    return f'<figure class="media-figure">{image}{figcaption}</figure>'


def render_media_shortcodes(
    content: str | None, assets: Mapping[int, Any]
) -> str | None:
    """Заменяет шорткоды на разметку. Неизвестные номера удаляются."""
    if not content:
        return content

    seen = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal seen
        seen += 1
        media_id = int(match.group("id"))
        asset = assets.get(media_id)
        if seen > MAX_SHORTCODES or asset is None:
            logger.warning("Media shortcode skipped: id=%s", media_id)
            return ""
        return _render_figure(asset, _parse_attrs(match.group("attrs")))

    content = WRAPPED_RE.sub(lambda m: m.group("code"), content)
    return SHORTCODE_RE.sub(replace, content)


async def expand_media_shortcodes(
    content: str | None, load_assets: AssetLoader
) -> str | None:
    """Загружает файлы одним запросом и подставляет их в текст."""
    ids = find_media_ids(content)
    if not ids:
        return content
    return render_media_shortcodes(content, await load_assets(ids))


def db_asset_loader(db: Any) -> AssetLoader:
    """Загрузчик файлов из БД для expand_media_shortcodes."""

    async def load(ids: Iterable[int]) -> dict[int, Any]:
        from sqlalchemy import select

        from app.models import MediaAsset

        result = await db.execute(select(MediaAsset).where(MediaAsset.id.in_(set(ids))))
        return {asset.id: asset for asset in result.scalars().all()}

    return load
