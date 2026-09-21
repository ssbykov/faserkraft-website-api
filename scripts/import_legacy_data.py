"""
scripts/import_legacy_data.py
Импорт данных из старого WordPress в PostgreSQL
"""
import asyncio
import csv
from pathlib import Path

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.models import Product, ProductCategory, ProductSpecification

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
        sort_counters: dict[int, int] = {}
        for row in reader:
            legacy_id = int(row["product_id"])
            product_id = legacy_to_new.get(legacy_id)
            if product_id is None:
                continue
            sort_counters[product_id] = sort_counters.get(product_id, 0) + 1
            spec = ProductSpecification(
                product_id=product_id,
                group_name=row["group_name"],
                parameter_name=row["parameter_name"],
                parameter_value=row.get("parameter_value", ""),
                sort_order=sort_counters[product_id],
            )
            session.add(spec)
    await session.commit()


async def main() -> None:
    async with AsyncSessionLocal() as session:
        print("1/3 Заполнение категорий...")
        category_map = await seed_categories(session)

        print("2/3 Импорт продуктов...")
        legacy_to_new = await import_products(session, category_map)
        print(f"   Импортировано продуктов: {len(legacy_to_new)}")

        print("3/3 Импорт характеристик...")
        await import_specifications(session, legacy_to_new)

    print("Импорт завершён успешно.")


if __name__ == "__main__":
    asyncio.run(main())
