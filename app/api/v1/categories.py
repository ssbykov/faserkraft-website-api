"""
app/api/v1/categories.py
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import ProductCategory
from app.schemas.schemas import ProductCategoryCreate, ProductCategoryOut
from app.api.deps import require_editor

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[ProductCategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductCategory).where(ProductCategory.is_published.is_(True)).order_by(ProductCategory.sort_order)
    )
    return result.scalars().all()


@router.get("/{slug}", response_model=ProductCategoryOut)
async def get_category(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProductCategory).where(ProductCategory.slug == slug))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена")
    return category


@router.post("", response_model=ProductCategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: ProductCategoryCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_editor),
):
    existing = await db.execute(select(ProductCategory).where(ProductCategory.slug == payload.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Категория с таким slug уже существует")

    category = ProductCategory(**payload.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category
