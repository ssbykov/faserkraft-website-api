"""
app/admin/menus.py
Регистрация моделей меню сайта в SQLAdmin.
"""

from sqladmin import ModelView

from app.models import Menu, MenuItem


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
        Menu.is_active,
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
        MenuItem.menu_id,
        MenuItem.is_visible,
        MenuItem.target_blank,
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