from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import Context, db


contexts_bp = Blueprint("contexts", __name__, url_prefix="/contextos")


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _context_from_form(context=None):
    """Llena un contexto con datos del formulario."""
    if context is None:
        context = Context()

    context.name = request.form.get("name", "").strip()
    context.number_people = max(_to_int(request.form.get("number_people"), 1), 1)
    context.children = max(_to_int(request.form.get("children"), 0), 0)
    context.adults = max(_to_int(request.form.get("adults"), 0), 0)
    context.elderly = max(_to_int(request.form.get("elderly"), 0), 0)
    context.gender = request.form.get("gender", "").strip() or None
    context.dependents_count = max(_to_int(request.form.get("dependents_count"), 0), 0)
    context.monthly_income = max(_to_float(request.form.get("monthly_income"), 0), 0)
    context.earners = max(_to_int(request.form.get("earners"), 1), 1)
    context.income_type = request.form.get("income_type", "fijo")
    context.consumption_level = request.form.get("consumption_level", "medio")
    context.preferences = request.form.get("preferences", "economico")
    context.diet = request.form.get("diet", "").strip() or None
    context.purchase_frequency = request.form.get("purchase_frequency", "semanal")
    return context


@contexts_bp.route("/", methods=["GET", "POST"])
def contexts():
    if request.method == "POST":
        context = _context_from_form()
        if not context.name:
            flash("El nombre del contexto es obligatorio.", "error")
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
        _context_from_form(context)
        if not context.name:
            flash("El nombre del contexto es obligatorio.", "error")
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
