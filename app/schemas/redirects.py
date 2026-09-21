"""
app/schemas/redirects.py
Pydantic v2 схема редиректа.
"""
from pydantic import BaseModel, ConfigDict


class RedirectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_path: str
    target_path: str
    http_status: int
