"""
app/admin/catalog.py
Регистрация моделей каталога товаров в SQLAdmin
"""

from sqlalchemy import func, select

from markupsafe import Markup, escape
from sqladmin import ModelView
from sqladmin.fields import FileField
from sqladmin.filters import BooleanFilter, ForeignKeyFilter
from sqlalchemy import func
from wtforms import SelectField

from app.models import MediaAsset
from app.models import (
    Product,
    ProductCategory,
    ProductDocument,
    ProductImage,
    ProductSpecification,
    SpecificationGroup,
    SpecificationParameter,
    ProductCardField,
)
from app.services.media import (
    MediaValidationError,
    delete_product_image_file,
    save_product_image,
)


class ProductCategoryAdmin(ModelView, model=ProductCategory):
    name = "Категория"
    name_plural = "Категории"
    icon = "fa-solid fa-layer-group"
    column_list = [
        ProductCategory.id,
        ProductCategory.slug,
        ProductCategory.name,
        ProductCategory.is_published,
        ProductCategory.sort_order,
    ]
    column_searchable_list = [ProductCategory.name, ProductCategory.slug]
    column_sortable_list = [ProductCategory.id, ProductCategory.sort_order]
    form_columns = [
        ProductCategory.slug,
        ProductCategory.name,
        ProductCategory.description,
        ProductCategory.sort_order,
        ProductCategory.is_published,
    ]
    can_export = True


class ProductAdmin(ModelView, model=Product):
    name = "Товар"
    name_plural = "Товары"
    icon = "fa-solid fa-box"
    column_list = [
        Product.id,
        Product.slug,
        Product.name,
        Product.category,
        Product.is_published,
        Product.updated_at,
    ]
    column_searchable_list = [Product.name, Product.slug]
    column_sortable_list = [Product.id, Product.updated_at]
    column_filters = [
        BooleanFilter(Product.is_published, title="Опубликован"),
    ]
    form_columns = [
        Product.category,
        Product.slug,
        Product.name,
        Product.short_description,
        Product.description,
        Product.membrane_material,
        Product.is_published,
        Product.seo_title,
        Product.seo_description,
    ]
    can_export = True


class SpecificationGroupAdmin(ModelView, model=SpecificationGroup):
    name = "Группа характеристик"
    name_plural = "Группы характеристик"
    icon = "fa-solid fa-folder-tree"
    column_list = [
        SpecificationGroup.id,
        SpecificationGroup.name,
        SpecificationGroup.sort_order,
    ]
    column_searchable_list = [SpecificationGroup.name]
    column_sortable_list = [SpecificationGroup.id, SpecificationGroup.sort_order]
    form_columns = [SpecificationGroup.name, SpecificationGroup.sort_order]


class SpecificationParameterAdmin(ModelView, model=SpecificationParameter):
    name = "Параметр характеристики"
    name_plural = "Параметры характеристик"
    icon = "fa-solid fa-sliders"
    column_list = [
        SpecificationParameter.id,
        SpecificationParameter.group,
        SpecificationParameter.name,
        SpecificationParameter.code,
        SpecificationParameter.sort_order,
        SpecificationParameter.is_filterable,
        SpecificationParameter.list_sort_order,
    ]
    column_sortable_list = [
        SpecificationParameter.id,
        SpecificationParameter.sort_order,
        SpecificationParameter.list_sort_order,
    ]
    column_filters = [
        ForeignKeyFilter(
            SpecificationParameter.group_id, SpecificationGroup.name, title="Группа"
        ),
        BooleanFilter(SpecificationParameter.is_filterable, title="Фильтр в списке"),
    ]
    form_columns = [
        SpecificationParameter.group,
        SpecificationParameter.name,
        SpecificationParameter.code,
        SpecificationParameter.sort_order,
        SpecificationParameter.is_filterable,
        SpecificationParameter.list_sort_order,
    ]


class ProductSpecificationAdmin(ModelView, model=ProductSpecification):
    name = "Характеристика"
    name_plural = "Характеристики"
    icon = "fa-solid fa-list-check"
    column_list = [
        ProductSpecification.id,
        ProductSpecification.product,
        ProductSpecification.parameter,
        ProductSpecification.value,
    ]
    column_searchable_list = [ProductSpecification.value]
    column_filters = [
        ForeignKeyFilter(
            ProductSpecification.product_id,
            Product.name,
            title="Товар",
        ),
        ForeignKeyFilter(
            ProductSpecification.parameter_id,
            SpecificationParameter.name,
            title="Параметр",
        ),
    ]
    form_columns = [
        ProductSpecification.product,
        ProductSpecification.parameter,
        ProductSpecification.value,
    ]
    form_ajax_refs = {
        "product": {"fields": ("name", "slug"), "order_by": "name"},
        "parameter": {"fields": ("name",), "order_by": "name"},
    }


PRODUCT_IMAGE_KIND_CHOICES = [
    ("cover", "Обложка карточки в каталоге"),
    ("gallery", "Фото в галерее"),
    ("drawing", "Чертёж"),
]


def _thumb(url: str | None) -> Markup:
    if not url:
        return Markup("")
    safe = escape(url)
    return Markup(
        f'<a href="{safe}" target="_blank" rel="noopener">'
        f'<img src="{safe}" alt="" style="max-height:48px;max-width:96px;'
        f'object-fit:contain;background:#fff"></a>'
    )


class MediaAssetAdmin(ModelView, model=MediaAsset):
    name = "Медиафайл"
    name_plural = "Медиафайлы"
    icon = "fa-solid fa-images"

    column_list = [
        MediaAsset.id,
        MediaAsset.file_url,
        MediaAsset.title,
        MediaAsset.alt_text,
        MediaAsset.created_at,
    ]
    column_labels = {
        MediaAsset.file_url: "Файл",
        MediaAsset.title: "Название",
        MediaAsset.alt_text: "Alt-текст",
        MediaAsset.created_at: "Загружен",
    }
    column_formatters = {MediaAsset.file_url: lambda m, a: _thumb(m.file_url)}
    column_formatters_detail = {MediaAsset.file_url: lambda m, a: _thumb(m.file_url)}
    column_searchable_list = [
        MediaAsset.title,
        MediaAsset.alt_text,
        MediaAsset.file_url,
    ]
    column_sortable_list = [MediaAsset.id, MediaAsset.created_at]
    column_default_sort = [(MediaAsset.id, True)]

    # file_url записывается после загрузки файла
    form_columns = [MediaAsset.title, MediaAsset.alt_text]
    form_args = {
        "title": {
            "label": "Название",
            "description": "Для поиска в админке. Если пусто - возьмётся имя файла.",
        },
        "alt_text": {
            "label": "Alt-текст",
            "description": "Краткое описание изображения для поисковиков и экранных дикторов.",
        },
    }

    async def scaffold_form(self, rules=None):
        form_class = await super().scaffold_form(rules)
        form_class.file = FileField(
            "Файл изображения",
            description=(
                "JPG, PNG, WebP или SVG. При редактировании оставьте пустым, "
                "чтобы сохранить текущий файл. Новый файл заменит изображение "
                "у всех товаров, где оно используется."
            ),
        )
        return form_class

    async def on_model_change(self, data, model, is_created, request):
        upload = data.pop("file", None)
        filename = getattr(upload, "filename", None)

        if not filename:
            if is_created:
                raise ValueError("Загрузите файл изображения.")
            return

        try:
            data["file_url"] = await save_product_image(upload)
        except MediaValidationError as exc:
            raise ValueError(str(exc)) from exc

        if not data.get("title"):
            data["title"] = filename.rsplit("/", 1)[-1][:255]

        # Старый файл удаляем только после успешного сохранения записи
        if not is_created:
            request.state.old_media_file_url = model.file_url

    async def after_model_change(self, data, model, is_created, request):
        old_url = getattr(request.state, "old_media_file_url", None)
        if old_url and old_url != model.file_url:
            delete_product_image_file(old_url)
        request.state.old_media_file_url = None

    async def on_model_delete(self, model, request):
        # Файл, который используется товарами, удалять нельзя
        async with self.session_maker() as session:
            used = await session.scalar(
                select(func.count())
                .select_from(ProductImage)
                .where(ProductImage.asset_id == model.id)
            )
        if used:
            raise ValueError(
                f"Файл используется у товаров ({used}). "
                "Сначала удалите привязки в разделе «Изображения»."
            )

        pending = getattr(request.state, "media_files_to_delete", [])
        pending.append(model.file_url)
        request.state.media_files_to_delete = pending

    async def after_model_delete(self, model, request):
        for url in getattr(request.state, "media_files_to_delete", []):
            delete_product_image_file(url)
        request.state.media_files_to_delete = []


class ProductImageAdmin(ModelView, model=ProductImage):
    name = "Изображение товара"
    name_plural = "Изображения товаров"
    icon = "fa-solid fa-image"

    column_list = [
        ProductImage.id,
        ProductImage.product,
        ProductImage.asset,
        ProductImage.kind,
        ProductImage.sort_order,
    ]
    column_labels = {
        ProductImage.product: "Товар",
        ProductImage.asset: "Файл",
        ProductImage.kind: "Назначение",
        ProductImage.sort_order: "Порядок",
    }
    column_formatters = {
        ProductImage.asset: lambda m, a: _thumb(m.asset.file_url)
        + Markup(" ")
        + escape(repr(m.asset)),
    }
    column_default_sort = [
        (ProductImage.product_id, False),
        (ProductImage.sort_order, False),
    ]
    column_sortable_list = [
        ProductImage.id,
        ProductImage.product_id,
        ProductImage.sort_order,
    ]
    column_filters = [
        ForeignKeyFilter(ProductImage.product_id, Product.name, title="Товар"),
    ]

    form_columns = [
        ProductImage.product,
        ProductImage.asset,
        ProductImage.kind,
        ProductImage.sort_order,
    ]
    form_overrides = {"kind": SelectField}
    form_args = {
        "product": {"label": "Товар"},
        "asset": {
            "label": "Файл",
            "description": "Загрузите файл заранее в разделе «Медиафайлы».",
        },
        "kind": {
            "label": "Назначение",
            "choices": PRODUCT_IMAGE_KIND_CHOICES,
            "description": (
                "Обложкой карточки в каталоге становится первое изображение "
                "с назначением «Обложка» (по порядку), иначе первое фото из "
                "галереи. Чертежи обложкой не бывают."
            ),
        },
        "sort_order": {"label": "Порядок", "description": "Меньше - выше."},
    }
    form_ajax_refs = {
        "product": {"fields": ("name", "slug"), "order_by": "name"},
        "asset": {"fields": ("title", "alt_text", "file_url"), "order_by": "id"},
    }


class ProductDocumentAdmin(ModelView, model=ProductDocument):
    name = "Документ"
    name_plural = "Документы"
    icon = "fa-solid fa-file-lines"
    column_list = [
        ProductDocument.id,
        ProductDocument.product,
        ProductDocument.document_type,
        ProductDocument.title,
        ProductDocument.file_url,
        ProductDocument.sort_order,
    ]
    form_columns = [
        ProductDocument.product,
        ProductDocument.document_type,
        ProductDocument.title,
        ProductDocument.file_url,
        ProductDocument.sort_order,
    ]


class ProductCardFieldAdmin(ModelView, model=ProductCardField):
    name = "Поле карточки"
    name_plural = "Поля карточки"
    icon = "fa-solid fa-id-card"
    column_list = [
        ProductCardField.id,
        ProductCardField.key,
        ProductCardField.label,
        ProductCardField.parameter,
        ProductCardField.sort_order,
        ProductCardField.is_active,
    ]
    column_sortable_list = [ProductCardField.sort_order, ProductCardField.key]
    form_columns = [
        ProductCardField.key,
        ProductCardField.label,
        ProductCardField.parameter,
        ProductCardField.sort_order,
        ProductCardField.is_active,
    ]
    form_ajax_refs = {
        "parameter": {"fields": ("name",), "order_by": "name"},
    }


CATALOG_VIEWS = [
    ProductCategoryAdmin,
    ProductAdmin,
    SpecificationGroupAdmin,
    SpecificationParameterAdmin,
    ProductSpecificationAdmin,
    ProductImageAdmin,
    MediaAssetAdmin,
    ProductDocumentAdmin,
    ProductCardFieldAdmin,
]
