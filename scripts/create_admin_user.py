"""
scripts/create_admin_user.py
Создание первого администратора для входа в /admin
Запуск: python -m scripts.create_admin_user
"""
import asyncio
import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models import User


async def main() -> None:
    email = input("Email администратора: ").strip().lower()
    full_name = input("Полное имя (необязательно): ").strip() or None
    password = getpass.getpass("Пароль: ")
    password_confirm = getpass.getpass("Повторите пароль: ")

    if password != password_confirm:
        print("Пароли не совпадают. Отмена.")
        return

    if len(password) < 8:
        print("Пароль должен быть не короче 8 символов. Отмена.")
        return

    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(User).where(User.email == email))
        user = existing.scalar_one_or_none()

        if user is not None:
            user.hashed_password = hash_password(password)
            user.role = "admin"
            user.is_active = True
            if full_name:
                user.full_name = full_name
            print(f"Пользователь {email} уже существовал — пароль и роль обновлены.")
        else:
            user = User(
                email=email,
                hashed_password=hash_password(password),
                full_name=full_name,
                role="admin",
                is_active=True,
            )
            session.add(user)
            print(f"Создан новый администратор: {email}")

        await session.commit()

    print("Готово. Теперь можно войти на /admin с этим email и паролем.")


if __name__ == "__main__":
    asyncio.run(main())
