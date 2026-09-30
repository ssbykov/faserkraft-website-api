"""
app/api/v1/pages.py
Публичные и административные эндпоинты контентных страниц.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models import Page, PageType, MenuItem, Menu
from app.schemas.pages import (
    PageListItem,
    PageOut,
    PageTreeItem,
)

router = APIRouter(prefix="/pages", tags=["pages"])


@router.get("", response_model=list[PageListItem])
async def list_pages(
    type: Optional[str] = Query(
        default=None,
        description="Фильтр по коду типа: page, article или case_study",
    ),
    parent_slug: Optional[str] = Query(
        default=None,
        description="Фильтр по slug родительской страницы",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Список опубликованных страниц с фильтрацией и пагинацией."""
    stmt = (
        select(Page)
        .options(selectinload(Page.page_type))
        .where(Page.status == "published")
        .order_by(Page.sort_order, Page.title)
    )

    if type:
        stmt = stmt.join(Page.page_type).where(PageType.code == type)

    if parent_slug:
        parent_result = await db.execute(select(Page).where(Page.slug == parent_slug))
        parent = parent_result.scalar_one_or_none()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Родительская страница не найдена",
            )
        stmt = stmt.where(Page.parent_id == parent.id)

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/tree", response_model=list[PageTreeItem])
async def get_pages_tree(db: AsyncSession = Depends(get_db)):
    """
    Дерево опубликованных страниц для навигации.

    Возвращает корневые опубликованные страницы с опубликованными дочерними
    страницами первого уровня. В ответе каждого пункта есть children.
    """
    stmt = (
        select(Page)
        .options(
            selectinload(Page.page_type),
            selectinload(Page.children).selectinload(Page.page_type),
        )
        .where(
            Page.status == "published",
            Page.parent_id.is_(None),
        )
        .order_by(Page.sort_order, Page.title)
    )

    result = await db.execute(stmt)
    root_pages = result.scalars().unique().all()

    def to_tree_item(page_obj: Page) -> PageTreeItem:
        children = sorted(
            (child for child in page_obj.children if child.status == "published"),
            key=lambda child: (child.sort_order, child.title),
        )

        return PageTreeItem(
            id=page_obj.id,
            slug=page_obj.slug,
            title=page_obj.title,
            status=page_obj.status,
            sort_order=page_obj.sort_order,
            parent_id=page_obj.parent_id,
            page_type=page_obj.page_type,
            children=[
                PageTreeItem(
                    id=child.id,
                    slug=child.slug,
                    title=child.title,
                    status=child.status,
                    sort_order=child.sort_order,
                    parent_id=child.parent_id,
                    page_type=child.page_type,
                    children=[],
                )
                for child in children
            ],
        )

    return [to_tree_item(page_obj) for page_obj in root_pages]


@router.get("/{slug}", response_model=PageOut)
async def get_page(slug: str, db: AsyncSession = Depends(get_db)):
    """Детальная опубликованная страница по slug."""
    stmt = (
        select(Page)
        .options(
            selectinload(Page.page_type),
            selectinload(Page.parent),
            selectinload(Page.images),
            selectinload(Page.children).selectinload(Page.page_type),
            selectinload(Page.documents),
        )
        .where(
            Page.slug == slug,
            Page.status == "published",
        )
    )

    result = await db.execute(stmt)
    page_obj = result.scalar_one_or_none()

    if page_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Страница не найдена",
        )

    menu_result = await db.execute(
        select(MenuItem)
        .join(Menu, Menu.id == MenuItem.menu_id)
        .options(selectinload(MenuItem.parent))
        .where(
            MenuItem.page_id == page_obj.id,
            MenuItem.is_visible.is_(True),
            Menu.is_active.is_(True),
            MenuItem.parent_id.is_not(None),
        )
        .order_by(Menu.code, MenuItem.sort_order, MenuItem.id)
    )

    menu_parent_labels = [
        item.parent.label
        for item in menu_result.scalars().all()
        if item.parent is not None and item.parent.is_visible
    ]

    page_out = PageOut.model_validate(page_obj)
    return page_out.model_copy(update={"menu_parent_labels": menu_parent_labels})






