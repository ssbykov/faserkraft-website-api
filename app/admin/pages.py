"""
app/admin/pages.py
Регистрация моделей контентных страниц в SQLAdmin
"""

from sqladmin import ModelView
from sqladmin.filters import StaticValuesFilter, ForeignKeyFilter

from app.models import Page, PageImage, PageType


class PageTypeAdmin(ModelView, model=PageType):
    name = "Тип страницы"
    name_plural = "Типы страниц"
    icon = "fa-solid fa-tags"
    column_list = [PageType.id, PageType.code, PageType.name, PageType.template]
    column_searchable_list = [PageType.code, PageType.name]
    form_columns = [PageType.code, PageType.name, PageType.template]


class PageAdmin(ModelView, model=Page):
    name = "Страница"
    name_plural = "Страницы"
    icon = "fa-solid fa-file-lines"
    column_list = [
        Page.id,
        Page.slug,
        Page.title,
        Page.page_type,
        Page.parent,
        Page.status,
        Page.updated_at,
    ]
    column_searchable_list = [Page.title, Page.slug]
    column_sortable_list = [Page.id, Page.sort_order, Page.updated_at]
    column_filters = [
        StaticValuesFilter(
            Page.status,
            values=[("published", "Опубликована"), ("draft", "Черновик")],
        ),
        ForeignKeyFilter(Page.page_type_id, PageType.name, title="Тип страницы"),
    ]
    form_columns = [
        Page.page_type,
        Page.parent,
        Page.slug,
        Page.title,
        Page.content,
        Page.status,
        Page.seo_title,
        Page.seo_description,
        Page.sort_order,
    ]
    form_ajax_refs = {
        "parent": {
            "fields": ("title", "slug"),
            "order_by": "title",
        },
    }
    can_export = True


class PageImageAdmin(ModelView, model=PageImage):
    name = "Изображение страницы"
    name_plural = "Изображения страниц"
    icon = "fa-solid fa-image"
    column_list = [
        PageImage.id,
        PageImage.page,
        PageImage.image_url,
        PageImage.is_cover,
        PageImage.sort_order,
    ]
    form_columns = [
        PageImage.page,
        PageImage.image_url,
        PageImage.alt_text,
        PageImage.is_cover,
        PageImage.sort_order,
    ]


PAGES_VIEWS = [
    PageTypeAdmin,
    PageAdmin,
    PageImageAdmin,
]
