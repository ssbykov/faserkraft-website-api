"""add cta fields to page types

Revision ID: 28f4549fce8d
Revises: 45bbf52079d2
Create Date: 2026-11-02 17:39:25.784531

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "28f4549fce8d"
down_revision: Union[str, None] = "45bbf52079d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "page_types", sa.Column("cta_eyebrow", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "page_types", sa.Column("cta_title", sa.String(length=500), nullable=True)
    )
    op.add_column("page_types", sa.Column("cta_text", sa.Text(), nullable=True))
    op.add_column(
        "page_types", sa.Column("cta_button", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "page_types", sa.Column("cta_href", sa.String(length=500), nullable=True)
    )
    page_types = sa.table(
        "page_types",
        sa.column("code", sa.String),
        sa.column("cta_eyebrow", sa.String),
        sa.column("cta_title", sa.String),
        sa.column("cta_text", sa.Text),
        sa.column("cta_button", sa.String),
        sa.column("cta_href", sa.String),
    )

    seeds = {
        "technology": (
            "Технологическая консультация",
            "Подберём технологию под ваш объект",
            "Расскажите о качестве исходной воды и требованиях к очистке — инженеры предложат схему на основе этой технологии.",
            "Обсудить технологию",
        ),
        "specification": (
            "Техническая документация",
            "Нужна спецификация под ваш проект?",
            "Укажите производительность и условия эксплуатации — подготовим спецификацию и расчёт для вашего объекта.",
            "Запросить спецификацию",
        ),
        "manual": (
            "Поддержка",
            "Остались вопросы по эксплуатации?",
            "Опишите ситуацию на установке — специалисты помогут разобраться с запуском, обслуживанием и промывкой модулей.",
            "Связаться со специалистом",
        ),
        "article": (
            "Остались вопросы",
            "Разберём вашу задачу вместе",
            "Если материал не ответил на ваш вопрос, опишите задачу — инженеры подскажут, какое решение подойдёт.",
            "Задать вопрос инженеру",
        ),
        "case_study": (
            "Похожий проект",
            "Нужно такое же решение на вашем объекте?",
            "Пришлите исходные данные по воде и производительности — подготовим расчёт по аналогии с этим проектом.",
            "Обсудить проект",
        ),
    }

    for code, (eyebrow, title, text, button) in seeds.items():
        op.execute(
            page_types.update()
            .where(page_types.c.code == code)
            .values(
                cta_eyebrow=eyebrow,
                cta_title=title,
                cta_text=text,
                cta_button=button,
                cta_href="/contact",
            )
        )


def downgrade() -> None:
    op.drop_column("page_types", "cta_href")
    op.drop_column("page_types", "cta_button")
    op.drop_column("page_types", "cta_text")
    op.drop_column("page_types", "cta_title")
    op.drop_column("page_types", "cta_eyebrow")
