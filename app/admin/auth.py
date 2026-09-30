"""
app/admin/auth.py
Авторизация администратора для SQLAdmin по таблице users
"""

from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from app.core.config import settings
from app.core.rate_limit import admin_login_limiter, client_ip
from app.core.security import hash_password, verify_password
from app.db.session import AsyncSessionLocal
from app.models import User

SESSION_USER_KEY = "admin_user_email"
ALLOWED_ROLES = ("admin", "editor")

# хеш-заглушка: время ответа не выдаёт, существует ли такой email
_DUMMY_HASH = hash_password("not-a-real-password")


class AdminAuth(AuthenticationBackend):
    def __init__(self, secret_key: str) -> None:
        super().__init__(secret_key=secret_key)
        self.middlewares = [
            Middleware(
                SessionMiddleware,
                secret_key=secret_key,
                session_cookie="fk_admin_session",
                max_age=settings.ADMIN_SESSION_MAX_AGE_SECONDS,
                same_site="strict",
                https_only=settings.IS_PRODUCTION,
            )
        ]

    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = str(form.get("username", "")).strip().lower()
        password = str(form.get("password", ""))[:256]

        ip_key = f"ip:{client_ip(request)}"
        email_key = f"email:{email}"
        if admin_login_limiter.is_limited(ip_key) or admin_login_limiter.is_limited(
            email_key
        ):
            return False

        user = None
        if email and password:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(User).where(User.email == email))
                user = result.scalar_one_or_none()

        hashed = user.hashed_password if user else _DUMMY_HASH
        password_ok = verify_password(password, hashed)

        if not (user and password_ok and user.is_active and user.role in ALLOWED_ROLES):
            admin_login_limiter.hit(ip_key)
            admin_login_limiter.hit(email_key)
            return False

        admin_login_limiter.reset(ip_key)
        admin_login_limiter.reset(email_key)
        request.session.clear()
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
        # роль и активность проверяются на каждом запросе
        return bool(user and user.is_active and user.role in ALLOWED_ROLES)


authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)
