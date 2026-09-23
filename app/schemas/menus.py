from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MenuItemTreeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    href: Optional[str] = None
    target_blank: bool
    children: list["MenuItemTreeOut"] = Field(default_factory=list)


class MenuTreeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    items: list[MenuItemTreeOut] = Field(default_factory=list)