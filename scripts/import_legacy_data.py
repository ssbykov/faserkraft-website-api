"""
scripts/import_legacy_data.py
Импорт данных из старого WordPress в PostgreSQL
"""
import asyncio
import csv
from pathlib import Path

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models import Product, ProductCategory, ProductSpecification, ProductImage

DATA_DIR = Path(__file__).resolve().parent.parent / "legacy_data"

CATEGORY_SEED = [
    {"slug": "ultrafiltracionnye-membrannye-moduli", "name": "Ультрафильтрационные мембранные модули"},
    {"slug": "pogruzhnoj-membrannyj-filtr", "name": "Погружные мембранные фильтры"},
]


async def seed_categories(session) -> dict[str, int]:
    slug_to_id: dict[str, int] = {}
    for cat in CATEGORY_SEED:
        existing = await session.execute(select(ProductCategory).where(ProductCategory.slug == cat["slug"]))
        obj = existing.scalar_one_or_none()
        if obj is None:
            obj = ProductCategory(**cat)
            session.add(obj)
            await session.flush()
        slug_to_id[cat["slug"]] = obj.id
    await session.commit()
    return slug_to_id


async def import_products(session, category_map: dict[str, int]) -> dict[int, int]:
    legacy_to_new: dict[int, int] = {}
    path = DATA_DIR / "products.csv"
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            legacy_id = int(row["product_id"])
            existing = await session.execute(select(Product).where(Product.legacy_wp_id == legacy_id))
            obj = existing.scalar_one_or_none()
            if obj is None:
                obj = Product(
                    legacy_wp_id=legacy_id,
                    slug=row["slug"],
                    name=row["title"],
                    category_id=category_map.get(row.get("category_slug", "")),
                    status="published",
                )
                session.add(obj)
                await session.flush()
            else:
                obj.slug = row["slug"]
                obj.name = row["title"]
                obj.category_id = category_map.get(row.get("category_slug", ""), obj.category_id)
            legacy_to_new[legacy_id] = obj.id
    await session.commit()
    return legacy_to_new


async def import_specifications(session, legacy_to_new: dict[int, int]) -> None:
    path = DATA_DIR / "product_specifications.csv"
    if not path.exists():
        print(f"Пропуск: {path} не найден")
        return

    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows_by_product: dict[int, list[dict]] = {}
        for row in reader:
            legacy_id = int(row["product_id"])
            product_id = legacy_to_new.get(legacy_id)
            if product_id is None:
                continue
            rows_by_product.setdefault(product_id, []).append(row)

    for product_id, rows in rows_by_product.items():
        await session.execute(
            ProductSpecification.__table__.delete().where(ProductSpecification.product_id == product_id)
        )
        for sort_order, row in enumerate(rows, start=1):
            spec = ProductSpecification(
                product_id=product_id,
                group_name=row["group_name"],
                parameter_name=row["parameter_name"],
                parameter_value=row.get("parameter_value", ""),
                sort_order=sort_order,
            )
            session.add(spec)
    await session.commit()


async def import_images(session, legacy_to_new: dict[int, int]) -> None:
    path = DATA_DIR / "product_images.csv"
    if not path.exists():
        print(f"Пропуск: {path} не найден")
        return

    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows_by_product: dict[int, list[dict]] = {}
        skipped = 0
        for row in reader:
            legacy_id = int(row["product_id"])
            product_id = legacy_to_new.get(legacy_id)
            if product_id is None:
                skipped += 1
                continue
            rows_by_product.setdefault(product_id, []).append(row)

    for product_id, rows in rows_by_product.items():
        await session.execute(
            ProductImage.__table__.delete().where(ProductImage.product_id == product_id)
        )
        for row in rows:
            image = ProductImage(
                product_id=product_id,
                image_url=row["image_url"],
                sort_order=int(row.get("sort_order", 0) or 0),
            )
            session.add(image)
    await session.commit()

    print(f"   Изображений импортировано для товаров: {len(rows_by_product)}")
    if skipped:
        print(f"   Пропущено строк (товар не найден): {skipped}")


async def main() -> None:
    async with AsyncSessionLocal() as session:
        print("1/4 Заполнение категорий...")
        category_map = await seed_categories(session)

        print("2/4 Импорт продуктов...")
        legacy_to_new = await import_products(session, category_map)
        print(f"   Импортировано продуктов: {len(legacy_to_new)}")

        print("3/4 Импорт характеристик...")
        await import_specifications(session, legacy_to_new)

        print("4/4 Импорт изображений...")
        await import_images(session, legacy_to_new)

        print("Импорт завершён успешно.")


if __name__ == "__main__":
    asyncio.run(main())
