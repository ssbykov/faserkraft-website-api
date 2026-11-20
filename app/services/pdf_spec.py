from collections import defaultdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.schemas.schemas import ProductOut

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_product_spec_pdf(product: ProductOut) -> bytes:
    sorted_specs = sorted(product.specifications, key=lambda s: s.sort_order)
    grouped: dict[str, list] = defaultdict(list)
    for spec in sorted_specs:
        group_name = (spec.group_name or "").strip() or "Основные характеристики"
        grouped[group_name].append(spec)

    template = _jinja_env.get_template("product_spec.html")
    html_str = template.render(product=product, grouped_specs=grouped)
    return HTML(string=html_str, base_url=str(TEMPLATES_DIR)).write_pdf()