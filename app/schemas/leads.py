"""
app/schemas/leads.py
Pydantic v2 схемы заявок с сайта.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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
