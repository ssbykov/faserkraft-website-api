import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def revalidate_homepage() -> None:
    """
    Просит Next.js сбросить cache данных и маршрута главной страницы.

    Ошибка webhook не должна отменять сохранение в SQLAdmin:
    данные уже успешно сохранены в PostgreSQL, а Next.js всё равно
    обновит их по ISR не позднее чем через 60 секунд.
    """
    if not (
        settings.FRONTEND_REVALIDATE_URL
        and settings.FRONTEND_REVALIDATE_SECRET
    ):
        logger.warning(
            "Homepage revalidation skipped: frontend webhook "
            "configuration is missing."
        )
        return

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                settings.FRONTEND_REVALIDATE_URL,
                headers={
                    "x-revalidate-secret": (
                        settings.FRONTEND_REVALIDATE_SECRET
                    ),
                },
            )
            response.raise_for_status()
    except httpx.HTTPError:
        logger.exception("Homepage revalidation request failed.")