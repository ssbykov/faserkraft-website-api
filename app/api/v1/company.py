from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.company import CompanyOut
from app.services.company import get_company

router = APIRouter(prefix="/company", tags=["company"])


@router.get("", response_model=CompanyOut | None)
async def read_company(db: AsyncSession = Depends(get_db)):
    return await get_company(db)
