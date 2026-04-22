from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Product(db.Model):
    """Producto de la canasta básica y su cantidad de referencia."""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=True)
    quantity_value = db.Column(db.Float, nullable=False, default=1.0)
    quantity_unit = db.Column(db.String(12), nullable=False, default="pza")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    prices = db.relationship(
        "StorePrice",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy=True,
    )

    @property
    def display_quantity(self):
        numeric_value = float(self.quantity_value or 0)
        value = int(numeric_value) if numeric_value.is_integer() else numeric_value
        return f"{value:g} {self.quantity_unit}"

    @property
    def normalized_quantity(self):
        unit = self.quantity_unit.lower()
        if unit == "kg":
            return self.quantity_value * 1000, "g"
        if unit == "g":
            return self.quantity_value, "g"
        if unit == "l":
            return self.quantity_value * 1000, "ml"
        if unit == "ml":
            return self.quantity_value, "ml"
        return self.quantity_value, self.quantity_unit

    @property
    def normalized_label(self):
        value, unit = self.normalized_quantity
        clean_value = int(value) if float(value).is_integer() else round(value, 2)
        return f"{clean_value:g} {unit}"

    @property
    def cheapest_price(self):
        if not self.prices:
            return None
        return min(self.prices, key=lambda item: item.price)

    @property
    def highest_price(self):
        if not self.prices:
            return None
        return max(self.prices, key=lambda item: item.price)

    @property
    def average_price(self):
        if not self.prices:
            return 0
        return sum(item.price for item in self.prices) / len(self.prices)

    def price_for_store(self, store_name):
        if not store_name:
            return None
        normalized_store = store_name.strip().lower()
        for price in self.prices:
            if price.store_name.strip().lower() == normalized_store:
                return price
        return None


class StorePrice(db.Model):
    """Precio de un producto en una tienda específica."""

    __tablename__ = "store_prices"
    __table_args__ = (
        db.UniqueConstraint("product_id", "store_name", name="uq_product_store"),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    store_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    product = db.relationship("Product", back_populates="prices")


class Context(db.Model):
    """Contexto socioeconómico usado para estimar el costo de consumo."""

    __tablename__ = "contexts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    number_people = db.Column(db.Integer, nullable=False, default=1)
    children = db.Column(db.Integer, nullable=False, default=0)
    adults = db.Column(db.Integer, nullable=False, default=1)
    elderly = db.Column(db.Integer, nullable=False, default=0)
    gender = db.Column(db.String(40), nullable=True)
    dependents_count = db.Column(db.Integer, nullable=False, default=0)
    monthly_income = db.Column(db.Float, nullable=False, default=0)
    earners = db.Column(db.Integer, nullable=False, default=1)
    income_type = db.Column(db.String(20), nullable=False, default="fijo")
    consumption_level = db.Column(db.String(20), nullable=False, default="medio")
    preferences = db.Column(db.String(20), nullable=False, default="economico")
    diet = db.Column(db.String(120), nullable=True)
    purchase_frequency = db.Column(db.String(20), nullable=False, default="semanal")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def composition_label(self):
        return f"{self.number_people} personas"
