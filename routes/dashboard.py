from flask import Blueprint, render_template, request

from catalogs import STORE_OPTIONS
from models import Context, Product
from services.calculations import build_dashboard_data


dashboard_bp = Blueprint("dashboard", __name__)


def _resolve_store_option(value):
    if not value:
        return None
    needle = str(value).strip().lower()
    for option in STORE_OPTIONS:
        if option.strip().lower() == needle:
            return option
    return None


@dashboard_bp.route("/dashboard")
def dashboard():
    products = Product.query.filter_by(is_basic_basket=True).order_by(Product.name.asc()).all()
    if not products:
        products = Product.query.order_by(Product.name.asc()).all()
    contexts = Context.query.order_by(Context.created_at.asc()).all()

    active_store = _resolve_store_option(request.args.get("store"))

    dashboard_data = build_dashboard_data(
        products=products,
        contexts=contexts,
        time_range="6",
        store_name=active_store,
    )

    return render_template(
        "dashboard.html",
        products=products,
        contexts=contexts,
        dashboard_data=dashboard_data,
        active_store=active_store,
    )
