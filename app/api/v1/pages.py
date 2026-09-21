"""
app/api/v1/pages.py
Публичные и административные эндпоинты контентных страниц.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import require_editor
from app.db.session import get_db
from app.models import Page, PageType
from app.schemas.pages import PageCreate, PageListItem, PageOut, PageUpdate

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


@router.get("/tree", response_model=list[PageListItem])
async def get_pages_tree(db: AsyncSession = Depends(get_db)):
    """
    Дерево опубликованных страниц для навигации.

    Возвращает опубликованные страницы верхнего уровня с опубликованными
    дочерними страницами первого уровня. У детей поле children не включается,
    поэтому ответ конечен и пригоден для меню.
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
    pages = result.scalars().unique().all()

    # SQLAlchemy relationship загружает всех детей. Оставляем опубликованных,
    # чтобы в меню не попадали черновики.
    for page_obj in pages:
        page_obj.children[:] = [
            child for child in page_obj.children if child.status == "published"
        ]
        page_obj.children.sort(key=lambda child: (child.sort_order, child.title))

    return pages


@router.get("/{slug}", response_model=PageOut)
async def get_page(slug: str, db: AsyncSession = Depends(get_db)):
    """Детальная опубликованная страница по slug."""
    stmt = (
        select(Page)
        .options(
            selectinload(Page.page_type),
            selectinload(Page.images),
            selectinload(Page.children).selectinload(Page.page_type),
        )
        .where(
            Page.slug == slug,
            Page.status == "published",
        )
    )
    result = await db.execute(stmt)
    page_obj = result.scalar_one_or_none()
    if not page_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Страница не найдена",
        )
    return page_obj


@router.post("", response_model=PageOut, status_code=status.HTTP_201_CREATED)
async def create_page(
    payload: PageCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_editor),
):
    """Создаёт новую контентную страницу. Доступно редактору."""
    existing = await db.execute(select(Page).where(Page.slug == payload.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Страница с таким slug уже существует",
        )

    page_type_result = await db.execute(
        select(PageType).where(PageType.id == payload.page_type_id)
    )
    if not page_type_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Указанный page_type_id не существует",
        )

    if payload.parent_id is not None:
        parent_result = await db.execute(select(Page).where(Page.id == payload.parent_id))
        if not parent_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанный parent_id не существует",
            )

    page_obj = Page(**payload.model_dump())
    db.add(page_obj)
    await db.commit()
    await db.refresh(page_obj, attribute_names=["page_type", "images", "children"])
    return page_obj


@router.patch("/{page_id}", response_model=PageOut)
async def update_page(
    page_id: int,
    payload: PageUpdate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_editor),
):
    """Частично обновляет страницу. Доступно редактору."""
    result = await db.execute(select(Page).where(Page.id == page_id))
    page_obj = result.scalar_one_or_none()
    if not page_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Страница не найдена",
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "slug" in update_data:
        existing = await db.execute(
            select(Page).where(
                Page.slug == update_data["slug"],
                Page.id != page_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Страница с таким slug уже существует",
            )

    if "page_type_id" in update_data:
        page_type_result = await db.execute(
            select(PageType).where(PageType.id == update_data["page_type_id"])
        )
        if not page_type_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанный page_type_id не существует",
            )

    if "parent_id" in update_data:
        parent_id = update_data["parent_id"]

        if parent_id == page_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Страница не может быть родителем самой себя",
            )

        if parent_id is not None:
            parent_result = await db.execute(select(Page).where(Page.id == parent_id))
            if not parent_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Указанный parent_id не существует",
                )

    for field, value in update_data.items():
        setattr(page_obj, field, value)

    await db.commit()
    await db.refresh(page_obj, attribute_names=["page_type", "images", "children"])
    return page_obj


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    page_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_editor),
):
    """Удаляет страницу без дочерних страниц. Доступно редактору."""
    result = await db.execute(select(Page).where(Page.id == page_id))
    page_obj = result.scalar_one_or_none()
    if not page_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Страница не найдена",
        )

    children_result = await db.execute(
        select(Page.id).where(Page.parent_id == page_id).limit(1)
    )
    if children_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Нельзя удалить страницу, у которой есть дочерние страницы",
        )

    await db.delete(page_obj)
    await db.commit()
