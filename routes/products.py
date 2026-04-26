from flask import Blueprint, flash, redirect, render_template, request, url_for

from catalogs import PRODUCT_CATEGORIES, STORE_FIELDS
from models import Product, StorePrice, db


products_bp = Blueprint("products", __name__, url_prefix="/productos")


def _to_float(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clean_prices(form):
    """Read fixed store prices and validate positive values."""
    cleaned = {}
    missing_stores = []
    for field in STORE_FIELDS:
        numeric_price = _to_float(form.get(field["field_name"]))
        if numeric_price <= 0:
            missing_stores.append(field["store"])
            continue
        cleaned[field["store"]] = numeric_price
    return cleaned, missing_stores


def _price_inputs(product=None):
    existing_prices = {}
    if product is not None:
        existing_prices = {price.store_name: price.price for price in product.prices}

    return [
        {
            "store": field["store"],
            "field_name": field["field_name"],
            "value": existing_prices.get(field["store"], ""),
        }
        for field in STORE_FIELDS
    ]


@products_bp.route("/", methods=["GET", "POST"])
def products():
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        prices, missing_stores = _clean_prices(request.form)

        product = Product(
            name=request.form.get("name", "").strip(),
            category=category,
            quantity_value=_to_float(request.form.get("quantity_value"), 1),
            quantity_unit=request.form.get("quantity_unit", "pza"),
        )

        if not product.name:
            flash("El nombre del producto es obligatorio.", "error")
            return redirect(url_for("products.products"))
        if category not in PRODUCT_CATEGORIES:
            flash("Selecciona una categoría válida.", "error")
            return redirect(url_for("products.products"))
        if product.quantity_value <= 0:
            flash("Captura una cantidad válida mayor a cero.", "error")
            return redirect(url_for("products.products"))
        if missing_stores:
            flash(f"Captura un precio válido para: {', '.join(missing_stores)}.", "error")
            return redirect(url_for("products.products"))

        for store_name, price in prices.items():
            product.prices.append(StorePrice(store_name=store_name, price=price))

        db.session.add(product)
        db.session.commit()
        flash("Producto agregado correctamente.", "success")
        return redirect(url_for("products.products"))

    all_products = Product.query.order_by(Product.name.asc()).all()
    return render_template(
        "products.html",
        products=all_products,
        categories=PRODUCT_CATEGORIES,
        store_fields=_price_inputs(),
    )


@products_bp.route("/<int:product_id>/editar", methods=["GET", "POST"])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        category = request.form.get("category", "").strip()
        prices, missing_stores = _clean_prices(request.form)

        product.name = request.form.get("name", "").strip()
        product.category = category
        product.quantity_value = _to_float(request.form.get("quantity_value"), 1)
        product.quantity_unit = request.form.get("quantity_unit", "pza")

        if not product.name:
            flash("El nombre del producto es obligatorio.", "error")
            return redirect(url_for("products.edit_product", product_id=product.id))
        if category not in PRODUCT_CATEGORIES:
            flash("Selecciona una categoría válida.", "error")
            return redirect(url_for("products.edit_product", product_id=product.id))
        if product.quantity_value <= 0:
            flash("Captura una cantidad válida mayor a cero.", "error")
            return redirect(url_for("products.edit_product", product_id=product.id))
        if missing_stores:
            flash(f"Captura un precio válido para: {', '.join(missing_stores)}.", "error")
            return redirect(url_for("products.edit_product", product_id=product.id))

        product.prices.clear()
        db.session.flush()
        for store_name, price in prices.items():
            product.prices.append(StorePrice(store_name=store_name, price=price))

        db.session.commit()
        flash("Producto actualizado correctamente.", "success")
        return redirect(url_for("products.products"))

    return render_template(
        "product_form.html",
        product=product,
        categories=PRODUCT_CATEGORIES,
        store_fields=_price_inputs(product),
    )


@products_bp.route("/<int:product_id>/eliminar", methods=["POST"])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Producto eliminado correctamente.", "success")
    return redirect(url_for("products.products"))
