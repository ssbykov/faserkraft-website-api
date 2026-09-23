from typing import Any

from sqladmin import ModelView
from starlette.requests import Request

from app.models import HomepageCard, HomepageSection
from app.services.revalidation import revalidate_homepage


class HomepageSectionAdmin(ModelView, model=HomepageSection):
    name = "Секция главной"
    name_plural = "Секции главной"
    icon = "fa-solid fa-house"

    column_list = [
        HomepageSection.id,
        HomepageSection.code,
        HomepageSection.eyebrow,
        HomepageSection.title,
        HomepageSection.sort_order,
        HomepageSection.is_visible,
        HomepageSection.updated_at,
    ]

    column_searchable_list = [
        HomepageSection.code,
        HomepageSection.eyebrow,
        HomepageSection.title,
    ]

    column_sortable_list = [
        HomepageSection.id,
        HomepageSection.code,
        HomepageSection.sort_order,
        HomepageSection.is_visible,
        HomepageSection.updated_at,
    ]

    column_filters = [
        HomepageSection.is_visible,
    ]

    form_columns = [
        HomepageSection.code,
        HomepageSection.eyebrow,
        HomepageSection.title,
        HomepageSection.description,
        HomepageSection.content,
        HomepageSection.button_label,
        HomepageSection.button_url,
        HomepageSection.secondary_button_label,
        HomepageSection.secondary_button_url,
        HomepageSection.settings,
        HomepageSection.sort_order,
        HomepageSection.is_visible,
    ]

    can_export = True
    page_size = 50

    async def after_model_change(
        self,
        data: dict[str, Any],
        model: HomepageSection,
        is_created: bool,
        request: Request,
    ) -> None:
        await revalidate_homepage()

    async def after_model_delete(
        self,
        model: HomepageSection,
        request: Request,
    ) -> None:
        await revalidate_homepage()


class HomepageCardAdmin(ModelView, model=HomepageCard):
    name = "Карточка главной"
    name_plural = "Карточки главной"
    icon = "fa-solid fa-table-cells-large"

    column_list = [
        HomepageCard.id,
        HomepageCard.section,
        HomepageCard.label,
        HomepageCard.title_override,
        HomepageCard.page,
        HomepageCard.product,
        HomepageCard.sort_order,
        HomepageCard.is_visible,
    ]

    column_searchable_list = [
        HomepageCard.label,
        HomepageCard.title_override,
        HomepageCard.description_override,
    ]

    column_sortable_list = [
        HomepageCard.id,
        HomepageCard.sort_order,
        HomepageCard.is_visible,
    ]

    column_filters = [
        HomepageCard.section_id,
        HomepageCard.is_visible,
    ]

    form_columns = [
        HomepageCard.section,
        HomepageCard.page,
        HomepageCard.product,
        HomepageCard.label,
        HomepageCard.title_override,
        HomepageCard.description_override,
        HomepageCard.image_url,
        HomepageCard.button_label,
        HomepageCard.button_url,
        HomepageCard.sort_order,
        HomepageCard.is_visible,
    ]

    form_ajax_refs = {
        "section": {
            "fields": ("code", "title"),
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
    page_size = 100

    async def after_model_change(
        self,
        data: dict[str, Any],
        model: HomepageSection,
        is_created: bool,
        request: Request,
    ) -> None:
        await revalidate_homepage()

    async def after_model_delete(
        self,
        model: HomepageSection,
        request: Request,
    ) -> None:
        await revalidate_homepage()


HOMEPAGE_VIEWS = [
    HomepageSectionAdmin,
    HomepageCardAdmin,
]
