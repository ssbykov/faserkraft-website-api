"""
app/admin/pages.py
Регистрация моделей контентных страниц в SQLAdmin
"""

from sqladmin import ModelView
from sqladmin.filters import ForeignKeyFilter, BooleanFilter

from app.models import Page, PageRelatedLink, PageType


class PageTypeAdmin(ModelView, model=PageType):
    name = "Тип страницы"
    name_plural = "Типы страниц"
    icon = "fa-solid fa-tags"
    column_list = [PageType.id, PageType.code, PageType.name, PageType.cta_title]
    column_searchable_list = [PageType.code, PageType.name]
    form_columns = [
        PageType.code,
        PageType.name,
        PageType.template,
        PageType.cta_eyebrow,
        PageType.cta_title,
        PageType.cta_text,
        PageType.cta_button,
        PageType.cta_href,
    ]
    column_labels = {
        PageType.cta_eyebrow: "CTA: надзаголовок",
        PageType.cta_title: "CTA: заголовок",
        PageType.cta_text: "CTA: текст",
        PageType.cta_button: "CTA: текст кнопки",
        PageType.cta_href: "CTA: ссылка кнопки",
    }


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
        Page.is_published,
        Page.noindex,
        Page.updated_at,
    ]
    column_searchable_list = [Page.title, Page.slug]
    column_sortable_list = [Page.id, Page.sort_order, Page.updated_at]
    column_filters = [
        BooleanFilter(Page.is_published, title="Опубликована"),
        BooleanFilter(Page.noindex, title="Не индексировать"),
        ForeignKeyFilter(Page.page_type_id, PageType.name, title="Тип страницы"),
    ]
    form_columns = [
        Page.page_type,
        Page.parent,
        Page.slug,
        Page.title,
        Page.content,
        Page.is_published,
        Page.seo_title,
        Page.seo_description,
        Page.noindex,
        Page.sort_order,
    ]
    column_labels = {
        Page.is_published: "Опубликована",
        Page.noindex: "Не индексировать",
    }
    form_ajax_refs = {
        "parent": {
            "fields": ("title", "slug"),
            "order_by": "title",
        },
    }
    can_export = True


class PageRelatedLinkAdmin(ModelView, model=PageRelatedLink):
    name = "Связанный раздел"
    name_plural = "Связанные разделы"
    icon = "fa-solid fa-link"
    column_list = [
        PageRelatedLink.id,
        PageRelatedLink.page,
        PageRelatedLink.related_page,
        PageRelatedLink.card_title,
        PageRelatedLink.label,
        PageRelatedLink.sort_order,
    ]
    column_sortable_list = [PageRelatedLink.id, PageRelatedLink.sort_order]
    column_default_sort = [
        (PageRelatedLink.page_id, False),
        (PageRelatedLink.sort_order, False),
    ]
    column_filters = [
        ForeignKeyFilter(PageRelatedLink.page_id, Page.title, title="Страница"),
    ]
    form_columns = [
        PageRelatedLink.page,
        PageRelatedLink.related_page,
        PageRelatedLink.card_title,
        PageRelatedLink.label,
        PageRelatedLink.sort_order,
    ]
    column_labels = {
        PageRelatedLink.page: "Страница",
        PageRelatedLink.related_page: "Связанная страница",
        PageRelatedLink.card_title: "Короткий заголовок карточки",
        PageRelatedLink.label: "Метка карточки",
        PageRelatedLink.sort_order: "Порядок",
    }
    form_ajax_refs = {
        "page": {"fields": ("title", "slug"), "order_by": "title"},
        "related_page": {"fields": ("title", "slug"), "order_by": "title"},
    }

    async def on_model_change(self, data, model, is_created, request):
        page = data.get("page")
        related = data.get("related_page")
        if (
            page is not None
            and related is not None
            and getattr(page, "id", page) == getattr(related, "id", related)
        ):
            raise ValueError("Страница не может ссылаться на саму себя")


PAGES_VIEWS = [
    PageTypeAdmin,
    PageAdmin,
    PageRelatedLinkAdmin,
]
