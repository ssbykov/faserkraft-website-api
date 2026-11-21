"""
app/models/company.py
Реквизиты компании (одна запись).
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class CompanyInfo(Base):
    __tablename__ = "company_info"

    id: Mapped[int] = mapped_column(primary_key=True)

    short_name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(500))

    inn: Mapped[Optional[str]] = mapped_column(String(12))
    kpp: Mapped[Optional[str]] = mapped_column(String(9))
    ogrn: Mapped[Optional[str]] = mapped_column(String(15))

    legal_address: Mapped[Optional[str]] = mapped_column(String(500))
    actual_address: Mapped[Optional[str]] = mapped_column(String(500))
    map_embed_url: Mapped[Optional[str]] = mapped_column(String(2000))

    phone: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    website: Mapped[Optional[str]] = mapped_column(String(255))

    bank_name: Mapped[Optional[str]] = mapped_column(String(255))
    bik: Mapped[Optional[str]] = mapped_column(String(9))
    settlement_account: Mapped[Optional[str]] = mapped_column(String(20))
    correspondent_account: Mapped[Optional[str]] = mapped_column(String(20))

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return self.short_name
