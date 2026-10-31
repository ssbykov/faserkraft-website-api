from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.yandex_token import YandexToken


class YandexTokensRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self) -> YandexToken | None:
        result = await self.session.execute(
            select(YandexToken).where(YandexToken.id == "main")
        )
        return result.scalar_one_or_none()

    async def save(
        self,
        access_token: str,
        refresh_token: str,
        expires_at: datetime | None,
    ) -> None:
        token = await self.get()
        if token is None:
            token = YandexToken(id="main")
            self.session.add(token)

        token.access_token = access_token
        token.refresh_token = refresh_token
        token.expires_at = expires_at
        token.updated_at = datetime.now(timezone.utc)
        await self.session.commit()