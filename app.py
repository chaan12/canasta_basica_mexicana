import os

from flask import Flask, redirect, url_for

from models import db
from routes.contexts import contexts_bp
from routes.dashboard import dashboard_bp
from routes.products import products_bp
from services.seed import normalize_catalogs, seed_database


def create_app():
    """Crea la aplicación Flask y prepara la base de datos SQLite."""
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    database_path = os.path.join(app.instance_path, "canasta_basica.db")
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "cambia-esta-clave-en-produccion"),
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{database_path}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(contexts_bp)

    @app.route("/")
    def index():
        return redirect(url_for("dashboard.dashboard"))

    with app.app_context():
        db.create_all()
        seed_database()
        normalize_catalogs()

    return app


app = create_app()


if __name__ == "__main__":
    # Ejecución local: python app.py
    # En PythonAnywhere, importa la variable "app" desde este archivo en el WSGI.
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host=host, port=port, debug=debug)
