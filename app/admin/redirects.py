"""
app/admin/redirects.py
Регистрация модели редиректов в SQLAdmin
"""
from sqladmin import ModelView

from app.models import Redirect


class RedirectAdmin(ModelView, model=Redirect):
    name = "Редирект"
    name_plural = "Редиректы"
    icon = "fa-solid fa-arrows-turn-right"
    column_list = [Redirect.id, Redirect.source_path, Redirect.target_path, Redirect.http_status, Redirect.is_active]
    column_searchable_list = [Redirect.source_path, Redirect.target_path]
    form_columns = [Redirect.source_path, Redirect.target_path, Redirect.http_status, Redirect.is_active]


REDIRECTS_VIEWS = [RedirectAdmin]
