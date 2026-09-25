"""
app/admin/catalog.py
Регистрация моделей каталога товаров в SQLAdmin
"""

from sqladmin import ModelView
from sqladmin.filters import StaticValuesFilter

from app.models import (
    Product,
    ProductCategory,
    ProductDocument,
    ProductImage,
    ProductSpecification,
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
        Product.status,
        Product.updated_at,
    ]
    column_searchable_list = [Product.name, Product.slug]
    column_sortable_list = [Product.id, Product.updated_at]
    column_filters = [
        StaticValuesFilter(
            Product.status,
            values=[("published", "Опубликован"), ("draft", "Черновик")],
        ),
    ]
    form_columns = [
        Product.category,
        Product.slug,
        Product.name,
        Product.short_description,
        Product.description,
        Product.membrane_material,
        Product.status,
        Product.seo_title,
        Product.seo_description,
    ]
    can_export = True


class ProductSpecificationAdmin(ModelView, model=ProductSpecification):
    name = "Характеристика"
    name_plural = "Характеристики"
    icon = "fa-solid fa-list-check"
    column_list = [
        ProductSpecification.id,
        ProductSpecification.product,
        ProductSpecification.group_name,
        ProductSpecification.parameter_name,
        ProductSpecification.parameter_value,
        ProductSpecification.sort_order,
    ]
    column_searchable_list = [
        ProductSpecification.parameter_name,
        ProductSpecification.parameter_value,
    ]
    column_sortable_list = [ProductSpecification.sort_order]
    form_columns = [
        ProductSpecification.product,
        ProductSpecification.group_name,
        ProductSpecification.parameter_name,
        ProductSpecification.parameter_value,
        ProductSpecification.sort_order,
    ]


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


CATALOG_VIEWS = [
    ProductCategoryAdmin,
    ProductAdmin,
    ProductSpecificationAdmin,
    ProductImageAdmin,
    ProductDocumentAdmin,
]
