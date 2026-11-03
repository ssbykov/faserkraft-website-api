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

from app.db.session import get_db
from app.models import (
    Product,
    ProductCategory,
    ProductSpecification,
    SpecificationParameter,
)
from app.schemas.products import ProductFiltersResponse, FilterOption
from app.schemas.schemas import (
    ProductListItem,
    ProductOut,
)

router = APIRouter(prefix="/products", tags=["products"])


def specs_with_parameter(name_pattern: str):
    """Характеристики, у которых название параметра подходит под шаблон."""
    return (
        select(ProductSpecification)
        .join(
            SpecificationParameter,
            SpecificationParameter.id == ProductSpecification.parameter_id,
        )
        .where(SpecificationParameter.name.ilike(name_pattern))
    )


def product_ids_by_spec(name_pattern: str, value_pattern: str):
    subq = specs_with_parameter(name_pattern).where(
        ProductSpecification.value.ilike(value_pattern)
    )
    return select(subq.subquery().c.product_id)


def material_condition(material: str):
    return (
        (Product.membrane_material.ilike(f"%{material}%"))
        | (Product.name.ilike(f"%{material}%"))
        | (Product.slug.ilike(f"%{material}%"))
        | Product.id.in_(product_ids_by_spec("%материал%", f"%{material}%"))
    )


def clean_area_number(area: str) -> str:
    """Оставляет только число: '8.0 м²' -> '8.0'."""
    return re.sub(r"[^\d.,]", "", area).replace(",", ".")


def area_condition(area: str):
    clean_num = clean_area_number(area)
    return (
        (Product.slug.ilike(f"%-{clean_num}-%"))
        | (Product.slug.ilike(f"%-{clean_num}p-%"))
        | (Product.name.ilike(f"%-{clean_num}-%"))
        | (Product.name.ilike(f"% {clean_num} м²%"))
        | Product.id.in_(product_ids_by_spec("%площадь%", f"%{clean_num}%"))
    )


def published_product_ids(category_slug: Optional[str]):
    stmt = select(Product.id).where(Product.is_published.is_(True))
    if category_slug:
        stmt = stmt.join(Product.category).where(
            ProductCategory.slug == category_slug
        )
    return stmt


async def distinct_spec_values(
    db: AsyncSession, product_ids, name_pattern: str
) -> list[str]:
    stmt = (
        select(distinct(ProductSpecification.value))
        .join(
            SpecificationParameter,
            SpecificationParameter.id == ProductSpecification.parameter_id,
        )
        .where(
            ProductSpecification.product_id.in_(product_ids),
            SpecificationParameter.name.ilike(name_pattern),
            ProductSpecification.value.is_not(None),
            ProductSpecification.value != "",
        )
    )
    result = await db.execute(stmt)
    return [value.strip() for value in result.scalars().all() if value and value.strip()]


def parse_area_num(val: str) -> float:
    nums = re.findall(r"\d+(?:[.,]\d+)?", val)
    return float(nums[0].replace(",", ".")) if nums else 0.0


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
        )
        .where(Product.is_published.is_(True))
        .order_by(Product.name)
    )

    if category_slug:
        stmt = stmt.join(Product.category).where(
            ProductCategory.slug == category_slug
        )

    if material:
        stmt = stmt.where(material_condition(material))

    if area:
        stmt = stmt.where(area_condition(area))

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

    # Материалы: с учётом выбранной категории и площади
    base_for_materials = published_product_ids(category_slug)
    if area:
        base_for_materials = base_for_materials.where(area_condition(area))

    raw_materials = await distinct_spec_values(db, base_for_materials, "%материал%")
    materials = [FilterOption(label=m, value=m) for m in sorted(set(raw_materials))]

    # Площади: с учётом выбранной категории и материала
    base_for_areas = published_product_ids(category_slug)
    if material:
        base_for_areas = base_for_areas.where(material_condition(material))

    raw_areas = await distinct_spec_values(db, base_for_areas, "%площадь%")
    areas = [
        FilterOption(label=a, value=a)
        for a in sorted(set(raw_areas), key=parse_area_num)
    ]

    return ProductFiltersResponse(materials=materials, areas=areas)


@router.get("/{slug}", response_model=ProductOut)
async def get_product(slug: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.specifications)
            .selectinload(ProductSpecification.parameter)
            .selectinload(SpecificationParameter.group),
            selectinload(Product.images),
            selectinload(Product.documents),
        )
        .where(Product.slug == slug, Product.is_published.is_(True))
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден"
        )
    return product