"""
app/admin/auth.py
Авторизация администратора для SQLAdmin по таблице users
"""
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from sqlalchemy import select

from app.core.config import settings
from app.core.security import verify_password
from app.db.session import AsyncSessionLocal
from app.models import User

SESSION_USER_KEY = "admin_user_email"


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = str(form.get("username", "")).strip().lower()
        password = str(form.get("password", ""))

        if not email or not password:
            return False

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if user is None or not user.is_active:
                return False

            if user.role not in ("admin", "editor"):
                return False

            if not verify_password(password, user.hashed_password):
                return False

        request.session.update({SESSION_USER_KEY: email})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        email = request.session.get(SESSION_USER_KEY)
        if not email:
            return False

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            return bool(user and user.is_active)


authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)
