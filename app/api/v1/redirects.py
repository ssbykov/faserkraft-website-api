"""
app/api/v1/redirects.py
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Redirect
from app.schemas.schemas import RedirectOut

router = APIRouter(prefix="/redirects", tags=["redirects"])


@router.get("", response_model=list[RedirectOut])
async def list_redirects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Redirect).where(Redirect.is_active.is_(True)))
    return result.scalars().all()
