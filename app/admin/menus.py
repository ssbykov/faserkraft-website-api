"""
app/admin/menus.py
Регистрация моделей меню сайта в SQLAdmin.
"""

from sqladmin import ModelView
from sqladmin.filters import BooleanFilter
from sqlalchemy import select
from sqlalchemy.orm import aliased

from app.models import Menu, MenuItem


class ParentMenuItemFilter:
    title = "Родитель"
    parameter_name = "parent_id"
    has_operator = False
    template = "sqladmin/filters/lookup_filter.html"

    async def lookups(self, request, model, run_query):
        child = aliased(MenuItem)
        stmt = (
            select(MenuItem.id, MenuItem.label, Menu.code)
            .join(Menu, Menu.id == MenuItem.menu_id)
            .where(MenuItem.id.in_(
                select(child.parent_id).where(child.parent_id.is_not(None))
            ))
            .order_by(Menu.code, MenuItem.sort_order)
        )
        rows = await run_query(stmt)
        return [("", "Все")] + [(str(r.id), f"{r.code} / {r.label}") for r in rows]

    async def get_filtered_query(self, query, value, model):
        if not value:
            return query
        return query.filter(MenuItem.parent_id == int(value))

class MenuAdmin(ModelView, model=Menu):
    name = "Меню"
    name_plural = "Меню"
    icon = "fa-solid fa-bars"

    column_list = [
        Menu.id,
        Menu.code,
        Menu.name,
        Menu.is_active,
        Menu.updated_at,
    ]
    column_searchable_list = [
        Menu.code,
        Menu.name,
    ]
    column_sortable_list = [
        Menu.id,
        Menu.code,
        Menu.name,
        Menu.is_active,
        Menu.updated_at,
    ]
    column_filters = [
        BooleanFilter(Menu.is_active),
    ]

    form_columns = [
        Menu.code,
        Menu.name,
        Menu.is_active,
    ]

    can_export = True


class MenuItemAdmin(ModelView, model=MenuItem):
    name = "Пункт меню"
    name_plural = "Пункты меню"
    icon = "fa-solid fa-list"

    column_list = [
        MenuItem.id,
        MenuItem.menu,
        MenuItem.parent,
        MenuItem.label,
        MenuItem.page,
        MenuItem.product,
        MenuItem.url,
        MenuItem.sort_order,
        MenuItem.is_visible,
        MenuItem.target_blank,
    ]
    column_searchable_list = [
        MenuItem.label,
        MenuItem.url,
    ]
    column_sortable_list = [
        MenuItem.id,
        MenuItem.sort_order,
        MenuItem.is_visible,
        MenuItem.target_blank,
    ]
    column_filters = [
        ParentMenuItemFilter(),
        BooleanFilter(MenuItem.is_visible),
        BooleanFilter(MenuItem.target_blank),
    ]

    form_columns = [
        MenuItem.menu,
        MenuItem.parent,
        MenuItem.label,
        MenuItem.page,
        MenuItem.product,
        MenuItem.url,
        MenuItem.target_blank,
        MenuItem.sort_order,
        MenuItem.is_visible,
    ]

    form_ajax_refs = {
        "menu": {
            "fields": ("code", "name"),
            "order_by": "code",
        },
        "parent": {
            "fields": ("label",),
            "order_by": "sort_order",
        },
        "page": {
            "fields": ("title", "slug"),
            "order_by": "title",
        },
        "product": {
            "fields": ("name", "slug"),
            "order_by": "name",
        },
    }

    can_export = True


MENUS_VIEWS = [
    MenuAdmin,
    MenuItemAdmin,
]
