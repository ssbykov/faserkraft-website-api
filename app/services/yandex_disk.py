import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiohttp

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.yandex_tokens import YandexTokensRepository

logger = logging.getLogger(__name__)

_token_lock = asyncio.Lock()
_EXPIRY_MARGIN = timedelta(minutes=5)


class YaDiskError(Exception):
    pass


class YaDisk:
    API_URL = "https://cloud-api.yandex.net/v1/disk/resources"
    TOKEN_URL = "https://oauth.yandex.ru/token"

    def __init__(self) -> None:
        self.folder = settings.YANDEX_DISK_BACKUP_FOLDER.strip("/")

    async def _request_new_tokens(
        self, session: aiohttp.ClientSession, refresh_token: str
    ) -> dict:
        if not (settings.YANDEX_DISK_CLIENT_ID and settings.YANDEX_DISK_CLIENT_SECRET):
            raise YaDiskError("Не заданы YANDEX_DISK_CLIENT_ID / YANDEX_DISK_CLIENT_SECRET.")

        async with session.post(
            self.TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": settings.YANDEX_DISK_CLIENT_ID,
                "client_secret": settings.YANDEX_DISK_CLIENT_SECRET,
            },
        ) as response:
            payload = await response.json(content_type=None)
            if response.status != 200 or "access_token" not in payload:
                logger.error("Ошибка обновления токена Яндекса: %s", payload)
                raise YaDiskError(
                    f"Не удалось обновить токен Яндекс.Диска (HTTP {response.status}). "
                    "Возможно, нужно заново получить refresh_token."
                )
            return payload

    async def _get_access_token(
        self, session: aiohttp.ClientSession, force_refresh: bool = False
    ) -> str:
        async with _token_lock:
            async with AsyncSessionLocal() as db:
                repo = YandexTokensRepository(db)
                stored = await repo.get()

                if stored and not force_refresh:
                    valid = (
                        stored.expires_at is None
                        or stored.expires_at - _EXPIRY_MARGIN > datetime.now(timezone.utc)
                    )
                    if valid:
                        return stored.access_token

                refresh_token = (
                    stored.refresh_token if stored else settings.YANDEX_DISK_REFRESH_TOKEN
                )
                if not refresh_token:
                    raise YaDiskError("Нет refresh_token для Яндекс.Диска.")

                payload = await self._request_new_tokens(session, refresh_token)

                expires_in = payload.get("expires_in")
                expires_at = (
                    datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
                    if expires_in
                    else None
                )
                await repo.save(
                    payload["access_token"],
                    payload.get("refresh_token") or refresh_token,
                    expires_at,
                )
                return payload["access_token"]

    async def _api(
        self,
        session: aiohttp.ClientSession,
        method: str,
        url: str,
        params: dict,
    ) -> tuple[int, dict]:
        for attempt in (0, 1):
            token = await self._get_access_token(session, force_refresh=attempt == 1)
            async with session.request(
                method,
                url,
                headers={"Authorization": f"OAuth {token}"},
                params=params,
            ) as response:
                if response.status == 401 and attempt == 0:
                    continue
                text = await response.text()
                try:
                    data = json.loads(text) if text else {}
                except ValueError:
                    data = {}
                return response.status, data
        raise YaDiskError("Не удалось авторизоваться на Яндекс.Диске.")

    async def _create_folder(self, session: aiohttp.ClientSession) -> None:
        status, _ = await self._api(session, "PUT", self.API_URL, {"path": self.folder})
        if status not in (201, 409):
            raise YaDiskError(f"Не удалось создать папку на Яндекс.Диске, статус: {status}")

    async def _get_upload_url(self, session: aiohttp.ClientSession, file_name: str) -> str:
        status, data = await self._api(
            session,
            "GET",
            f"{self.API_URL}/upload",
            {"path": f"{self.folder}/{file_name}", "overwrite": "true"},
        )
        href = str(data.get("href", ""))
        if status != 200 or not href:
            raise YaDiskError(f"Не удалось получить ссылку загрузки, статус: {status}")
        return href

    async def upload_backup(self, file_path: Path) -> None:
        timeout = aiohttp.ClientTimeout(total=settings.YANDEX_DISK_TIMEOUT_SECONDS)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            await self._create_folder(session)
            upload_url = await self._get_upload_url(session, file_path.name)
            with file_path.open("rb") as source:
                async with session.put(upload_url, data=source) as response:
                    if response.status not in (201, 202):
                        raise YaDiskError(
                            f"Ошибка загрузки файла на Яндекс.Диск, статус: {response.status}"
                        )