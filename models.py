from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Product(db.Model):
    """Basic basket product and its reference presentation."""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=True)
    presentation = db.Column(db.String(160), nullable=True)
    quantity_value = db.Column(db.Float, nullable=False, default=1.0)
    quantity_unit = db.Column(db.String(12), nullable=False, default="pza")
    source_key = db.Column(db.String(160), nullable=True, index=True)
    is_basic_basket = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    prices = db.relationship(
        "StorePrice",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy=True,
    )

    @property
    def display_quantity(self):
        if self.presentation:
            return self.presentation
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

    @property
    def price_variance(self):
        if not self.prices:
            return 0
        values = [item.price for item in self.prices]
        return max(values) - min(values)

    def price_for_store(self, store_name):
        if not store_name:
            return None
        normalized_store = store_name.strip().lower()
        for price in self.prices:
            if price.store_name.strip().lower() == normalized_store:
                return price
        return None


class StorePrice(db.Model):
    """Product price for a specific store."""

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
    """Household context used to estimate consumption cost."""

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
    def child_count(self):
        return max(int(self.children or 0), 0)

    @property
    def adult_count(self):
        adults = max(int(self.adults or 0), 0)
        return max(adults, 1)

    @property
    def people_count(self):
        return self.adult_count + self.child_count

    @property
    def household_type_label(self):
        if self.child_count > 0:
            return "Familia"
        if self.adult_count > 1:
            return "Pareja"
        return "Vive solo"

    @property
    def composition_label(self):
        return f"{self.adult_count} adultos · {self.child_count} niños"
