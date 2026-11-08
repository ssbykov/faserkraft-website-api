"""
app/api/v1/products.py
Публичные эндпоинты каталога продукции
"""

import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import Numeric, cast, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, selectinload

from app.db.session import get_db
from app.models import (
    Product,
    ProductCategory,
    ProductSpecification,
    SpecificationGroup,
    SpecificationParameter,
    ProductCardField,
)
from app.schemas.products import (
    FilterGroup,
    FilterOption,
    ProductFiltersResponse,
    CardValue,
)
from app.schemas.schemas import ProductListItem, ProductOut
from app.services.shortcodes import db_asset_loader, expand_media_shortcodes

router = APIRouter(prefix="/products", tags=["products"])

FILTER_PREFIX = "f_"
LEADING_NUMBER = re.compile(r"\s*(\d+(?:[.,]\d+)?)")


def parse_spec_filters(request: Request) -> dict[int, str]:
    """?f_12=ПС&f_13=3 -> {12: 'ПС', 13: '3'}"""
    result: dict[int, str] = {}
    for key, value in request.query_params.items():
        suffix = key[len(FILTER_PREFIX) :]
        if key.startswith(FILTER_PREFIX) and suffix.isdigit() and value.strip():
            result[int(suffix)] = value.strip()
    return result


def spec_exists(parameter_id: int, value: str):
    """EXISTS: у товара параметр имеет точно такое значение."""
    return (
        exists()
        .where(
            ProductSpecification.product_id == Product.id,
            ProductSpecification.parameter_id == parameter_id,
            func.trim(ProductSpecification.value) == value,
        )
        .correlate(Product)
    )


def filtered_product_ids(
    category_slug: Optional[str],
    spec_filters: dict[int, str],
    exclude_parameter_id: Optional[int] = None,
):
    stmt = select(Product.id).where(Product.is_published.is_(True))
    if category_slug:
        stmt = stmt.join(Product.category).where(ProductCategory.slug == category_slug)
    for parameter_id, value in spec_filters.items():
        if parameter_id != exclude_parameter_id:
            stmt = stmt.where(spec_exists(parameter_id, value))
    return stmt


async def distinct_values(
    db: AsyncSession, product_ids, parameter_id: int
) -> list[str]:
    value = func.trim(ProductSpecification.value)
    stmt = (
        select(value)
        .where(
            ProductSpecification.parameter_id == parameter_id,
            ProductSpecification.product_id.in_(product_ids),
            value != "",
        )
        .distinct()
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


def natural_key(value: str):
    """Сначала значения с числом (по числу), затем текстовые."""
    match = LEADING_NUMBER.match(value)
    if match:
        return (0, float(match.group(1).replace(",", ".")), value.lower())
    return (1, 0.0, value.lower())


def sort_expressions(parameter_id: int):
    """Число из начала значения, затем текст; пустые значения в конец."""
    value = (
        select(func.trim(ProductSpecification.value))
        .where(
            ProductSpecification.product_id == Product.id,
            ProductSpecification.parameter_id == parameter_id,
        )
        .correlate(Product)
        .scalar_subquery()
    )
    first_number = func.substring(value, r"^\s*(\d+([.,]\d+)?)")
    number = cast(func.replace(first_number, ",", "."), Numeric)
    return [number.asc().nulls_last(), func.lower(value).asc().nulls_last()]


async def get_card_fields(db: AsyncSession) -> list[ProductCardField]:
    stmt = (
        select(ProductCardField)
        .where(ProductCardField.is_active.is_(True))
        .order_by(ProductCardField.sort_order, ProductCardField.id)
    )
    return list((await db.execute(stmt)).scalars().all())


def build_card(product: Product, fields: list[ProductCardField]) -> list[CardValue]:
    if not fields:
        return []
    values = {s.parameter_id: (s.value or "").strip() for s in product.specifications}
    card = []
    for field in fields:
        value = values.get(field.parameter_id)
        if value:
            card.append(
                CardValue(
                    key=field.key,
                    label=field.label or field.parameter.name,
                    value=value,
                )
            )
    return card


@router.get("", response_model=list[ProductListItem])
async def list_products(
    request: Request,
    category_slug: Optional[str] = Query(
        default=None, description="Фильтр по slug категории"
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    spec_filters = parse_spec_filters(request)
    card_fields = await get_card_fields(db)  # активные, по sort_order

    options = [contains_eager(Product.category), selectinload(Product.images)]
    if card_fields:
        # Грузим только характеристики, которые нужны карточке
        options.append(
            selectinload(
                Product.specifications.and_(
                    ProductSpecification.parameter_id.in_(
                        list({f.parameter_id for f in card_fields})
                    )
                )
            )
        )

    # Сортировка только по параметрам полей карточки, в порядке sort_order полей
    order_by = []
    seen_parameter_ids: set[int] = set()
    for field in card_fields:
        if field.parameter_id not in seen_parameter_ids:
            seen_parameter_ids.add(field.parameter_id)
            order_by.extend(sort_expressions(field.parameter_id))
    order_by.append(Product.id)  # стабильный порядок между страницами

    stmt = (
        select(Product)
        .outerjoin(Product.category)
        .options(*options)
        .where(Product.is_published.is_(True))
        .order_by(*order_by)
    )

    if category_slug:
        stmt = stmt.where(ProductCategory.slug == category_slug)
    for parameter_id, value in spec_filters.items():
        stmt = stmt.where(spec_exists(parameter_id, value))

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)

    items = []
    for product in result.scalars().unique().all():
        item = ProductListItem.model_validate(product)
        item.card = build_card(product, card_fields)
        items.append(item)
    return items


@router.get("/filters", response_model=ProductFiltersResponse)
async def get_product_filters(
    request: Request,
    category_slug: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Фильтры по параметрам с is_filterable=true; опции учитывают остальные фильтры."""
    spec_filters = parse_spec_filters(request)

    params_stmt = (
        select(SpecificationParameter.id, SpecificationParameter.name)
        .join(
            SpecificationGroup, SpecificationGroup.id == SpecificationParameter.group_id
        )
        .where(SpecificationParameter.is_filterable.is_(True))
        .order_by(
            SpecificationGroup.sort_order,
            SpecificationParameter.sort_order,
            SpecificationParameter.id,
        )
    )
    params = (await db.execute(params_stmt)).all()

    groups: list[FilterGroup] = []
    for parameter_id, name in params:
        base = filtered_product_ids(
            category_slug, spec_filters, exclude_parameter_id=parameter_id
        )
        values = await distinct_values(db, base, parameter_id)
        if values:
            groups.append(
                FilterGroup(
                    id=parameter_id,
                    name=name,
                    options=[
                        FilterOption(label=v, value=v)
                        for v in sorted(set(values), key=natural_key)
                    ],
                )
            )
    return ProductFiltersResponse(filters=groups)


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
    product_out = ProductOut.model_validate(product)
    description = await expand_media_shortcodes(
        product_out.description, db_asset_loader(db)
    )
    return product_out.model_copy(update={"description": description})
