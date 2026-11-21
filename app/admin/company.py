from sqladmin import ModelView

from app.models import CompanyInfo


class CompanyAdmin(ModelView, model=CompanyInfo):
    name = "Реквизиты компании"
    name_plural = "Реквизиты компании"
    icon = "fa-solid fa-building"
    can_delete = False
    column_list = [
        CompanyInfo.id,
        CompanyInfo.short_name,
        CompanyInfo.inn,
        CompanyInfo.phone,
        CompanyInfo.email,
    ]
    form_columns = [
        CompanyInfo.short_name,
        CompanyInfo.full_name,
        CompanyInfo.inn,
        CompanyInfo.kpp,
        CompanyInfo.ogrn,
        CompanyInfo.legal_address,
        CompanyInfo.actual_address,
        CompanyInfo.map_embed_url,
        CompanyInfo.phone,
        CompanyInfo.email,
        CompanyInfo.website,
        CompanyInfo.bank_name,
        CompanyInfo.bik,
        CompanyInfo.settlement_account,
        CompanyInfo.correspondent_account,
    ]

    column_labels = {
        CompanyInfo.map_embed_url: "URL встроенной Яндекс Карты",
    }

    form_widget_args = {
        "map_embed_url": {
            "placeholder": "https://yandex.ru/map-widget/v1/?...",
        },
    }


COMPANY_VIEWS = [CompanyAdmin]
