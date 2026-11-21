import re
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.company import get_company

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"

_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)

CONTACTS_RE = re.compile(
    r"\{\{\s*company\s*:\s*contacts\s*\}\}",
    re.IGNORECASE,
)

# Редактор может обернуть отдельный шорткод в <p>.
WRAPPED_CONTACTS_RE = re.compile(
    r"<p\b[^>]*>\s*" r"(?P<code>\{\{\s*company\s*:\s*contacts\s*\}\})" r"\s*</p>",
    re.IGNORECASE,
)


def split_phones(value: str | None) -> list[dict[str, str]]:
    phones: list[dict[str, str]] = []

    for part in (value or "").split(","):
        text = part.strip()
        if not text:
            continue

        number = re.sub(r"\D", "", text)
        if not number:
            continue

        if len(number) == 11 and number.startswith("8"):
            number = "7" + number[1:]

        international = text.startswith("+") or (
            len(number) == 11 and number.startswith("7")
        )

        phones.append(
            {
                "text": text,
                "href": f"tel:{'+' if international else ''}{number}",
            }
        )

    return phones


async def expand_company_shortcodes(
    content: str | None,
    db: AsyncSession,
) -> str | None:
    if not content or not CONTACTS_RE.search(content):
        return content

    company = await get_company(db)
    contacts_html = ""

    if company:
        address = (company.actual_address or "").strip() or (
            company.legal_address or ""
        ).strip()

        maps_url = (
            "https://yandex.ru/maps/?" + urlencode({"text": address}) if address else ""
        )

        template = _jinja_env.get_template("company_contacts.html")
        contacts_html = template.render(
            company=company,
            address=address,
            maps_url=maps_url,
            phones=split_phones(company.phone),
            map_embed_url=normalize_map_embed_url(company.map_embed_url),
        )

    content = WRAPPED_CONTACTS_RE.sub(
        lambda match: match.group("code"),
        content,
    )

    return CONTACTS_RE.sub(
        lambda match: contacts_html,
        content,
    )


def normalize_map_embed_url(value: str | None) -> str | None:
    if not value:
        return None

    url = value.strip()

    try:
        parsed = urlsplit(url)
    except ValueError:
        return None

    if (
        parsed.scheme != "https"
        or parsed.netloc != "yandex.ru"
        or not parsed.path.startswith("/map-widget/")
    ):
        return None

    return url
