"""
app/admin/users.py
Регистрация модели пользователей в SQLAdmin
"""
from sqladmin import ModelView

from app.models import User


class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user-shield"
    column_list = [User.id, User.email, User.full_name, User.role, User.is_active]
    column_searchable_list = [User.email, User.full_name]
    form_columns = [User.email, User.full_name, User.role, User.is_active]
    can_create = False
    can_delete = False


USERS_VIEWS = [UserAdmin]
