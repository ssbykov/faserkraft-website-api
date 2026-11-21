from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CompanyInfo
from app.schemas.company import CompanyOut


async def get_company(db: AsyncSession) -> CompanyOut | None:
    result = await db.execute(select(CompanyInfo).order_by(CompanyInfo.id).limit(1))
    company = result.scalar_one_or_none()
    return CompanyOut.model_validate(company) if company else None