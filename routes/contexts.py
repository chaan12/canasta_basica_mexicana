from math import isfinite

from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import Context, db


contexts_bp = Blueprint("contexts", __name__, url_prefix="/contextos")
MAX_HOUSEHOLD_MEMBERS = 20
MAX_MONTHLY_INCOME = 10000000


def _normalize_number(value):
    return str(value or "").replace("$", "").replace(",", "").replace(" ", "").strip()


def _read_int(field_name, label, default, errors):
    raw_value = request.form.get(field_name)
    if raw_value is None or str(raw_value).strip() == "":
        return default
    normalized_value = _normalize_number(raw_value)
    try:
        value = float(normalized_value)
    except ValueError:
        errors.append(f"{label} debe ser un número válido.")
        return default
    if not isfinite(value):
        errors.append(f"{label} debe ser un número válido.")
        return default
    if not value.is_integer():
        errors.append(f"{label} debe ser un número entero.")
    return int(value)


def _read_float(field_name, label, default, errors):
    raw_value = request.form.get(field_name)
    if raw_value is None or str(raw_value).strip() == "":
        return default
    try:
        value = float(_normalize_number(raw_value))
    except ValueError:
        errors.append(f"{label} debe ser un número válido.")
        return default
    if not isfinite(value):
        errors.append(f"{label} debe ser un número válido.")
        return default
    return value


def _context_from_form(context=None):
    """Populate a context with sanitized form data."""
    if context is None:
        context = Context()

    errors = []
    context.name = request.form.get("name", "").strip()
    adults = _read_int("adults", "Adultos", 1, errors)
    children = _read_int("children", "Niños", 0, errors)
    monthly_income = _read_float("monthly_income", "Ingreso mensual", 0, errors)
    earners = _read_int("earners", "Personas con ingreso", 1, errors)

    if adults < 1:
        errors.append("El hogar debe tener al menos un adulto.")
        adults = 1
    if children < 0:
        errors.append("El número de niños no puede ser negativo.")
        children = 0
    if adults + children > MAX_HOUSEHOLD_MEMBERS:
        errors.append(f"El hogar no puede superar {MAX_HOUSEHOLD_MEMBERS} integrantes.")
    if monthly_income < 0:
        errors.append("El ingreso mensual no puede ser negativo.")
        monthly_income = 0
    if monthly_income > MAX_MONTHLY_INCOME:
        errors.append("El ingreso mensual está fuera del rango permitido.")
        monthly_income = MAX_MONTHLY_INCOME
    if earners < 1:
        errors.append("Debe existir al menos una persona con ingreso.")
        earners = 1
    if earners > adults:
        errors.append("Las personas con ingreso no pueden superar el número de adultos.")
        earners = adults

    context.adults = adults
    context.children = children
    context.number_people = adults + children
    context.elderly = 0
    context.gender = None
    context.dependents_count = children
    context.monthly_income = monthly_income
    context.earners = earners
    context.income_type = request.form.get("income_type", "fijo")
    context.consumption_level = request.form.get("consumption_level", "medio")
    context.preferences = request.form.get("preferences", "economico")
    context.diet = request.form.get("diet", "").strip() or None
    context.purchase_frequency = request.form.get("purchase_frequency", "semanal")
    return context, errors


def _context_errors(context):
    errors = []
    if context.adults < 1:
        errors.append("El hogar debe tener al menos un adulto.")
    if context.children < 0:
        errors.append("El número de niños no puede ser negativo.")
    if context.adults + context.children > MAX_HOUSEHOLD_MEMBERS:
        errors.append(f"El hogar no puede superar {MAX_HOUSEHOLD_MEMBERS} integrantes.")
    if context.earners > context.adults:
        errors.append("Las personas con ingreso no pueden superar el número de adultos.")
    return errors


@contexts_bp.route("/", methods=["GET", "POST"])
def contexts():
    if request.method == "POST":
        context, form_errors = _context_from_form()
        if not context.name:
            flash("El nombre del contexto es obligatorio.", "error")
            return redirect(url_for("contexts.contexts"))
        errors = form_errors + _context_errors(context)
        for error in errors:
            flash(error, "error")
        if errors:
            return redirect(url_for("contexts.contexts"))

        db.session.add(context)
        db.session.commit()
        flash("Contexto agregado correctamente.", "success")
        return redirect(url_for("contexts.contexts"))

    all_contexts = Context.query.order_by(Context.created_at.desc()).all()
    return render_template("contexts.html", contexts=all_contexts)


@contexts_bp.route("/<int:context_id>/editar", methods=["GET", "POST"])
def edit_context(context_id):
    context = Context.query.get_or_404(context_id)

    if request.method == "POST":
        context, form_errors = _context_from_form(context)
        if not context.name:
            flash("El nombre del contexto es obligatorio.", "error")
            return redirect(url_for("contexts.edit_context", context_id=context.id))
        errors = form_errors + _context_errors(context)
        for error in errors:
            flash(error, "error")
        if errors:
            return redirect(url_for("contexts.edit_context", context_id=context.id))

        db.session.commit()
        flash("Contexto actualizado correctamente.", "success")
        return redirect(url_for("contexts.contexts"))

    return render_template("context_form.html", context=context)


@contexts_bp.route("/<int:context_id>/eliminar", methods=["POST"])
def delete_context(context_id):
    context = Context.query.get_or_404(context_id)
    db.session.delete(context)
    db.session.commit()
    flash("Contexto eliminado correctamente.", "success")
    return redirect(url_for("contexts.contexts"))
