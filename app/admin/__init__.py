"""
app/admin/__init__.py
Сборка административной панели SQLAdmin: подключение авторизации и всех view
"""

from sqladmin import Admin

from app.admin.auth import authentication_backend
from app.admin.catalog import CATALOG_VIEWS
from app.admin.leads import LEADS_VIEWS
from app.admin.menus import MENUS_VIEWS
from app.admin.pages import PAGES_VIEWS
from app.admin.redirects import REDIRECTS_VIEWS
from app.admin.users import USERS_VIEWS
from app.db.session import engine


def setup_admin(app) -> Admin:
    admin = Admin(
        app,
        engine,
        authentication_backend=authentication_backend,
        title="Faserkraft — Админка сайта",
    )

    for view in [
        *CATALOG_VIEWS,
        *PAGES_VIEWS,
        *LEADS_VIEWS,
        *REDIRECTS_VIEWS,
        *USERS_VIEWS,
        *MENUS_VIEWS,
    ]:
        admin.add_view(view)

    return admin
