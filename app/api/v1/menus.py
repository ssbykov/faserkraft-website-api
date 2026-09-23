from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models import Menu, MenuItem
from app.schemas.menus import MenuItemTreeOut, MenuTreeOut

router = APIRouter(prefix="/menus", tags=["menus"])


def get_item_href(item: MenuItem) -> Optional[str]:
    if item.url:
        return item.url

    if item.product is not None:
        return f"/produktsiya/{item.product.slug}"

    if item.page is not None:
        return f"/{item.page.slug}"

    return None


def to_tree_item(item: MenuItem) -> MenuItemTreeOut:
    visible_children = sorted(
        (child for child in item.children if child.is_visible),
        key=lambda child: (child.sort_order, child.id),
    )

    return MenuItemTreeOut(
        id=item.id,
        label=item.label,
        href=get_item_href(item),
        target_blank=item.target_blank,
        children=[to_tree_item(child) for child in visible_children],
    )


@router.get("/{code}", response_model=MenuTreeOut)
async def get_menu(
        code: str,
        db: AsyncSession = Depends(get_db),
) -> MenuTreeOut:
    """
    Возвращает активное публичное меню по его коду.

    В ответ включаются только видимые корневые пункты и видимые дочерние
    элементы. Вложенность загружается до второго уровня.
    """
    stmt = (
        select(Menu)
        .options(
            selectinload(Menu.items)
            .selectinload(MenuItem.page),
            selectinload(Menu.items)
            .selectinload(MenuItem.product),
            selectinload(Menu.items)
            .selectinload(MenuItem.children)
            .selectinload(MenuItem.page),
            selectinload(Menu.items)
            .selectinload(MenuItem.children)
            .selectinload(MenuItem.product),
        )
        .where(
            Menu.code == code,
            Menu.is_active.is_(True),
        )
    )

    result = await db.execute(stmt)
    menu = result.scalar_one_or_none()

    if menu is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Меню не найдено",
        )

    root_items = sorted(
        (
            item
            for item in menu.items
            if item.parent_id is None and item.is_visible
        ),
        key=lambda item: (item.sort_order, item.id),
    )

    return MenuTreeOut(
        code=menu.code,
        name=menu.name,
        items=[to_tree_item(item) for item in root_items],
    )
