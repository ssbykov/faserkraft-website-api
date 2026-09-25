"""
app/api/v1/products.py
Публичные и административные эндпоинты каталога продукции
"""
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import require_editor
from app.db.session import get_db
from app.models import Product, ProductCategory, ProductSpecification
from app.schemas.products import ProductFiltersResponse, FilterOption
from app.schemas.schemas import (
    ProductCreate,
    ProductListItem,
    ProductOut,
    ProductUpdate,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductListItem])
async def list_products(
    category_slug: Optional[str] = Query(
        default=None, description="Фильтр по slug категории"
    ),
    material: Optional[str] = Query(
        default=None, description="Фильтр по материалу"
    ),
    area: Optional[str] = Query(default=None, description="Фильтр по площади"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.images),
            selectinload(Product.specifications),
        )
        .where(Product.status == "published")
        .order_by(Product.name)
    )

    if category_slug:
        stmt = stmt.join(Product.category).where(
            ProductCategory.slug == category_slug
        )

    # Фильтрация по материалу
    if material:
        stmt = stmt.where(
            (Product.membrane_material.ilike(f"%{material}%"))
            | (Product.name.ilike(f"%{material}%"))
            | (Product.slug.ilike(f"%{material}%"))
            | (
                Product.id.in_(
                    select(ProductSpecification.product_id).where(
                        ProductSpecification.parameter_name.ilike(
                            "%материал%"
                        ),
                        ProductSpecification.parameter_value.ilike(
                            f"%{material}%"
                        ),
                    )
                )
            )
        )

    # Фильтрация по площади
    if area:
        # Извлекаем только числовое значение (например '8' из '8.0 м²')
        clean_num = re.sub(r"[^\d.,]", "", area).replace(",", ".")
        stmt = stmt.where(
            (Product.slug.ilike(f"%-{clean_num}-%"))
            | (Product.slug.ilike(f"%-{clean_num}p-%"))
            | (Product.name.ilike(f"%-{clean_num}-%"))
            | (Product.name.ilike(f"% {clean_num} м²%"))
            | (
                Product.id.in_(
                    select(ProductSpecification.product_id).where(
                        ProductSpecification.parameter_name.ilike(
                            "%площадь%"
                        ),
                        ProductSpecification.parameter_value.ilike(
                            f"%{clean_num}%"
                        ),
                    )
                )
            )
        )

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    return result.scalars().unique().all()


@router.get("/filters", response_model=ProductFiltersResponse)
async def get_product_filters(
    category_slug: Optional[str] = Query(default=None),
    material: Optional[str] = Query(default=None),
    area: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Возвращает контекстно-зависимые опции фильтрации (материалы и площади) из базы данных."""

    def parse_area_num(val: str) -> float:
        nums = re.findall(r"\d+(?:[.,]\d+)?", val)
        return float(nums[0].replace(",", ".")) if nums else 0.0

    # 1. Запрос доступных материалов (с учётом выбранной категории и площади)
    base_prod_for_mat = (
        select(Product.id)
        .where(Product.status == "published")
    )
    if category_slug:
        base_prod_for_mat = base_prod_for_mat.join(Product.category).where(
            ProductCategory.slug == category_slug
        )
    if area:
        clean_num = re.sub(r"[^\d.,]", "", area).replace(",", ".")
        base_prod_for_mat = base_prod_for_mat.where(
            (Product.slug.ilike(f"%-{clean_num}-%"))
            | (Product.slug.ilike(f"%-{clean_num}p-%"))
            | (Product.name.ilike(f"%-{clean_num}-%"))
            | (Product.name.ilike(f"% {clean_num} м²%"))
            | (
                Product.id.in_(
                    select(ProductSpecification.product_id).where(
                        ProductSpecification.parameter_name.ilike("%площадь%"),
                        ProductSpecification.parameter_value.ilike(f"%{clean_num}%"),
                    )
                )
            )
        )

    # Собираем материалы для отфильтрованного набора товаров
    mat_stmt = (
        select(distinct(ProductSpecification.parameter_value))
        .where(
            ProductSpecification.product_id.in_(base_prod_for_mat),
            ProductSpecification.parameter_name.ilike("%материал%"),
            ProductSpecification.parameter_value.is_not(None),
            ProductSpecification.parameter_value != "",
        )
    )
    mat_res = await db.execute(mat_stmt)
    raw_materials = mat_res.scalars().all()

    materials = [
        FilterOption(label=m.strip(), value=m.strip())
        for m in sorted(raw_materials)
        if m and m.strip()
    ]

    # 2. Запрос доступных площадей (с учётом выбранной категории и материала)
    base_prod_for_area = (
        select(Product.id)
        .where(Product.status == "published")
    )
    if category_slug:
        base_prod_for_area = base_prod_for_area.join(Product.category).where(
            ProductCategory.slug == category_slug
        )
    if material:
        base_prod_for_area = base_prod_for_area.where(
            (Product.membrane_material.ilike(f"%{material}%"))
            | (Product.name.ilike(f"%{material}%"))
            | (Product.slug.ilike(f"%{material}%"))
            | (
                Product.id.in_(
                    select(ProductSpecification.product_id).where(
                        ProductSpecification.parameter_name.ilike("%материал%"),
                        ProductSpecification.parameter_value.ilike(f"%{material}%"),
                    )
                )
            )
        )

    area_stmt = (
        select(distinct(ProductSpecification.parameter_value))
        .where(
            ProductSpecification.product_id.in_(base_prod_for_area),
            ProductSpecification.parameter_name.ilike("%площадь%"),
            ProductSpecification.parameter_value.is_not(None),
            ProductSpecification.parameter_value != "",
        )
    )
    area_res = await db.execute(area_stmt)
    raw_areas = area_res.scalars().all()

    sorted_raw_areas = sorted(
        [a.strip() for a in raw_areas if a and a.strip()],
        key=parse_area_num,
    )

    areas = [
        FilterOption(label=a, value=a)
        for a in sorted_raw_areas
        if a
    ]

    return ProductFiltersResponse(materials=materials, areas=areas)

@router.get("/{slug}", response_model=ProductOut)
async def get_product(slug: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.specifications),
            selectinload(Product.images),
            selectinload(Product.documents),
        )
        .where(Product.slug == slug)
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден"
        )
    return product


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_editor),
):
    existing = await db.execute(select(Product).where(Product.slug == payload.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Продукт с таким slug уже существует",
        )

    product = Product(**payload.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.patch("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_editor),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден"
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    return product
