from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HomepageCardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str | None = None
    title: str
    description: str | None = None
    image_url: str | None = None
    href: str | None = None
    button_label: str | None = None


class HomepageSectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    eyebrow: str | None = None
    title: str | None = None
    description: str | None = None
    content: str | None = None

    button_label: str | None = None
    button_url: str | None = None
    secondary_button_label: str | None = None
    secondary_button_url: str | None = None

    settings: dict[str, Any] | None = None
    cards: list[HomepageCardOut] = Field(default_factory=list)


class HomepageOut(BaseModel):
    sections: list[HomepageSectionOut] = Field(default_factory=list)