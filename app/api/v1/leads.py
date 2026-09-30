"""
app/api/v1/leads.py
Приём заявок с сайта. Просмотр и обработка заявок — только в SQLAdmin.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import client_ip, leads_global_limiter, leads_ip_limiter
from app.db.session import get_db
from app.models import LeadRequest
from app.schemas.schemas import LeadRequestCreate, LeadRequestOut
from app.services.notifications import notify_new_lead

router = APIRouter(prefix="/leads", tags=["leads"])

MAX_LENGTHS = {"name": 100, "phone": 32, "email": 254, "message": 5000}


def enforce_lead_limits(request: Request) -> None:
    ip = client_ip(request)
    if leads_ip_limiter.is_limited(ip) or leads_global_limiter.is_limited("global"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много заявок. Попробуйте позже.",
            headers={"Retry-After": "600"},
        )
    leads_ip_limiter.hit(ip)
    leads_global_limiter.hit("global")


@router.post(
    "",
    response_model=LeadRequestOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_lead_limits)],
)
async def create_lead(
    payload: LeadRequestCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump()
    for field, limit in MAX_LENGTHS.items():
        value = data.get(field)
        if isinstance(value, str) and len(value) > limit:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Поле {field} длиннее {limit} символов",
            )
    # статус задаёт только сервер, клиент его выбрать не может
    data.pop("status", None)

    lead = LeadRequest(**data)
    db.add(lead)
    await db.commit()
    await db.refresh(lead)

    background_tasks.add_task(
        notify_new_lead, lead.id, lead.name, lead.phone, lead.email, lead.message
    )
    return lead
