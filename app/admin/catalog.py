"""
app/admin/catalog.py
Регистрация моделей каталога товаров в SQLAdmin
"""

from sqladmin import ModelView
from sqladmin.filters import BooleanFilter, ForeignKeyFilter

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


class ProductImageAdmin(ModelView, model=ProductImage):
    name = "Изображение"
    name_plural = "Изображения"
    icon = "fa-solid fa-image"
    column_list = [
        ProductImage.id,
        ProductImage.product,
        ProductImage.image_url,
        ProductImage.sort_order,
    ]
    form_columns = [
        ProductImage.product,
        ProductImage.image_url,
        ProductImage.sort_order,
    ]


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
    ProductDocumentAdmin,
    ProductCardFieldAdmin,
]
