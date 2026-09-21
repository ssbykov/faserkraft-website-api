"""
app/api/v1/leads.py
Приём заявок с сайта
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.models import LeadRequest
from app.schemas.schemas import LeadRequestCreate, LeadRequestOut
from app.api.deps import require_editor
from app.services.notifications import notify_new_lead

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadRequestOut, status_code=status.HTTP_201_CREATED)
async def create_lead(
    payload: LeadRequestCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    lead = LeadRequest(**payload.model_dump())
    db.add(lead)
    await db.commit()
    await db.refresh(lead)

    background_tasks.add_task(notify_new_lead, lead.id, lead.name, lead.phone, lead.email, lead.message)
    return lead


@router.get("", response_model=list[LeadRequestOut])
async def list_leads(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_editor),
):
    result = await db.execute(select(LeadRequest).order_by(LeadRequest.created_at.desc()))
    return result.scalars().all()


@router.patch("/{lead_id}/status", response_model=LeadRequestOut)
async def update_lead_status(
    lead_id: int,
    new_status: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_editor),
):
    result = await db.execute(select(LeadRequest).where(LeadRequest.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")

    lead.status = new_status
    await db.commit()
    await db.refresh(lead)
    return lead
