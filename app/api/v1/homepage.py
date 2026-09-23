from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models import HomepageCard, HomepageSection
from app.schemas.homepage import (
    HomepageCardOut,
    HomepageOut,
    HomepageSectionOut,
)

router = APIRouter(
    prefix="/homepage",
    tags=["homepage"],
)


def get_card_href(card: HomepageCard) -> str | None:
    """
    Правило ссылки:
    1. Ручной button_url имеет высший приоритет.
    2. Product создаёт ссылку на каталог.
    3. Page создаёт ссылку на CMS-страницу.
    """
    if card.button_url:
        return card.button_url

    if card.product is not None:
        return f"/produktsiya/{card.product.slug}"

    if card.page is not None:
        return f"/{card.page.slug}"

    return None


def get_card_title(card: HomepageCard) -> str:
    """
    title_override позволяет задать компактный заголовок для homepage,
    не изменяя H1 связанной страницы или название продукта.
    """
    if card.title_override:
        return card.title_override

    if card.product is not None:
        return card.product.name

    if card.page is not None:
        return card.page.title

    return ""


def to_card_out(card: HomepageCard) -> HomepageCardOut:
    return HomepageCardOut(
        id=card.id,
        label=card.label,
        title=get_card_title(card),
        description=card.description_override,
        image_url=card.image_url,
        href=get_card_href(card),
        button_label=card.button_label,
    )


@router.get(
    "",
    response_model=HomepageOut,
    summary="Получить управляемое содержимое главной страницы",
)
async def get_homepage(
    db: AsyncSession = Depends(get_db),
) -> HomepageOut:
    stmt = (
        select(HomepageSection)
        .options(
            selectinload(HomepageSection.cards).selectinload(
                HomepageCard.page
            ),
            selectinload(HomepageSection.cards).selectinload(
                HomepageCard.product
            ),
        )
        .where(HomepageSection.is_visible.is_(True))
        .order_by(
            HomepageSection.sort_order.asc(),
            HomepageSection.id.asc(),
        )
    )

    result = await db.execute(stmt)
    sections = result.scalars().unique().all()

    return HomepageOut(
        sections=[
            HomepageSectionOut(
                id=section.id,
                code=section.code,
                eyebrow=section.eyebrow,
                title=section.title,
                description=section.description,
                content=section.content,
                button_label=section.button_label,
                button_url=section.button_url,
                secondary_button_label=section.secondary_button_label,
                secondary_button_url=section.secondary_button_url,
                settings=section.settings,
                cards=[
                    to_card_out(card)
                    for card in section.cards
                    if card.is_visible
                ],
            )
            for section in sections
        ],
    )