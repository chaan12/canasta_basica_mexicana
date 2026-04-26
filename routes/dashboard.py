from flask import Blueprint, render_template

from models import Context, Product
from services.calculations import build_dashboard_data


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def dashboard():
    products = Product.query.filter_by(is_basic_basket=True).order_by(Product.name.asc()).all()
    if not products:
        products = Product.query.order_by(Product.name.asc()).all()
    contexts = Context.query.order_by(Context.created_at.asc()).all()

    dashboard_data = build_dashboard_data(
        products=products,
        contexts=contexts,
        time_range="6",
    )

    return render_template(
        "dashboard.html",
        products=products,
        contexts=contexts,
        dashboard_data=dashboard_data,
    )
