"""
app/admin/leads.py
Регистрация модели заявок в SQLAdmin
"""
from sqladmin import ModelView

from app.models import LeadRequest


class LeadRequestAdmin(ModelView, model=LeadRequest):
    name = "Заявка"
    name_plural = "Заявки"
    icon = "fa-solid fa-envelope-open-text"
    column_list = [LeadRequest.id, LeadRequest.name, LeadRequest.phone, LeadRequest.email, LeadRequest.product_id, LeadRequest.status, LeadRequest.created_at]
    column_sortable_list = [LeadRequest.created_at]
    column_filters = [LeadRequest.status]
    form_columns = [LeadRequest.name, LeadRequest.phone, LeadRequest.email, LeadRequest.message, LeadRequest.product_id, LeadRequest.status]
    can_create = False


LEADS_VIEWS = [LeadRequestAdmin]
