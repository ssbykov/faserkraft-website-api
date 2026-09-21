"""
app/services/notifications.py
Уведомление менеджера о новой заявке
"""
import logging
from typing import Optional

import httpx

logger = logging.getLogger("faserkraft.notifications")

TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""


async def notify_new_lead(
    lead_id: int,
    name: str,
    phone: Optional[str],
    email: Optional[str],
    message: Optional[str],
) -> None:
    text = (
        f"Новая заявка №{lead_id}\n"
        f"Имя: {name}\n"
        f"Телефон: {phone or '-'}\n"
        f"E-mail: {email or '-'}\n"
        f"Сообщение: {message or '-'}"
    )

    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})
        except Exception as exc:
            logger.error("Не удалось отправить уведомление в Telegram: %s", exc)
    else:
        logger.info("Заявка получена (уведомления не настроены): %s", text)
