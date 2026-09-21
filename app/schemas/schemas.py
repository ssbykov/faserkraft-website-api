"""
app/schemas/schemas.py
Pydantic v2 схемы запросов/ответов
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProductCategoryBase(BaseModel):
    slug: str
    name: str
    description: Optional[str] = None
    sort_order: int = 0
    is_published: bool = True


class ProductCategoryCreate(ProductCategoryBase):
    pass


class ProductCategoryOut(ProductCategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ProductSpecificationBase(BaseModel):
    group_name: str
    parameter_name: str
    parameter_value: Optional[str] = None
    sort_order: int = 0


class ProductSpecificationCreate(ProductSpecificationBase):
    pass


class ProductSpecificationOut(ProductSpecificationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ProductImageBase(BaseModel):
    image_url: str
    sort_order: int = 0


class ProductImageOut(ProductImageBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ProductDocumentBase(BaseModel):
    document_type: Optional[str] = None
    title: Optional[str] = None
    file_url: str
    sort_order: int = 0


class ProductDocumentOut(ProductDocumentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ProductBase(BaseModel):
    slug: str
    name: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    membrane_material: Optional[str] = None
    status: str = "published"
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None


class ProductCreate(ProductBase):
    category_id: Optional[int] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    membrane_material: Optional[str] = None
    status: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    category_id: Optional[int] = None


class ProductListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    name: str
    short_description: Optional[str] = None
    status: str
    category: Optional[ProductCategoryOut] = None
    images: list[ProductImageOut] = Field(default_factory=list)


class ProductOut(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
    category: Optional[ProductCategoryOut] = None
    specifications: list[ProductSpecificationOut] = Field(default_factory=list)
    images: list[ProductImageOut] = Field(default_factory=list)
    documents: list[ProductDocumentOut] = Field(default_factory=list)


class LeadRequestCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    email: Optional[EmailStr] = None
    message: Optional[str] = None
    source_url: Optional[str] = None
    product_id: Optional[int] = None


class LeadRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    phone: Optional[str]
    email: Optional[str]
    message: Optional[str]
    status: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: Optional[str]
    role: str
    is_active: bool


class RedirectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    source_path: str
    target_path: str
    http_status: int
