"""
app/models/redirects.py
Модель редиректов со старых URL на новые
"""
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Redirect(Base):
    __tablename__ = "redirects"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_path: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    target_path: Mapped[str] = mapped_column(String(500), nullable=False)
    http_status: Mapped[int] = mapped_column(Integer, default=301)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
