from sqlalchemy import inspect, text

from models import Context, Product, StorePrice, db
from services.catalog_importer import load_basket_catalog


LEGACY_CATEGORY_MAP = {
    "Cereales": "Cereales y derivados",
    "Proteína": "Proteínas animales",
    "Proteina": "Proteínas animales",
    "Verduras": "Frutas y verduras",
}

LEGACY_STORE_MAP = {
    "Soriana": "Bodega Aurrera",
    "Mercado local": "Chedraui",
}


def ensure_database_schema():
    inspector = inspect(db.engine)
    if not inspector.has_table("products"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("products")}
    migrations = {
        "presentation": "ALTER TABLE products ADD COLUMN presentation VARCHAR(160)",
        "source_key": "ALTER TABLE products ADD COLUMN source_key VARCHAR(160)",
        "is_basic_basket": "ALTER TABLE products ADD COLUMN is_basic_basket BOOLEAN NOT NULL DEFAULT 0",
    }

    with db.engine.begin() as connection:
        for column_name, statement in migrations.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))


def seed_database():
    sync_basic_basket_catalog()
    seed_default_contexts()


def sync_basic_basket_catalog():
    catalog = load_basket_catalog()
    products = catalog.get("products", [])
    if not products:
        return

    for item in products:
        source_key = item["source_key"]
        product = Product.query.filter_by(source_key=source_key).first()
        if product is None:
            product = Product(
                source_key=source_key,
                name=item["name"],
                is_basic_basket=True,
            )
            db.session.add(product)

        product.name = item["name"]
        product.category = item.get("category")
        product.presentation = item.get("presentation")
        product.quantity_value = item.get("quantity_value") or 1
        product.quantity_unit = item.get("quantity_unit") or "pza"
        product.source_key = source_key
        product.is_basic_basket = True

        valid_stores = set(item.get("prices", {}).keys())
        existing_prices = {price.store_name: price for price in product.prices}
        for store_name, price in item.get("prices", {}).items():
            store_price = existing_prices.get(store_name)
            if store_price is None:
                product.prices.append(StorePrice(store_name=store_name, price=price))
            else:
                store_price.price = price

        for store_price in list(product.prices):
            if store_price.store_name not in valid_stores:
                db.session.delete(store_price)

    db.session.commit()


def seed_default_contexts():
    if Context.query.first():
        return

    contexts = [
        Context(
            name="Familia urbana",
            number_people=4,
            children=1,
            adults=2,
            elderly=1,
            gender="Mixto",
            dependents_count=2,
            monthly_income=18000,
            earners=2,
            income_type="fijo",
            consumption_level="medio",
            preferences="economico",
            diet="Mixta",
            purchase_frequency="semanal",
        ),
        Context(
            name="Estudiante independiente",
            number_people=1,
            children=0,
            adults=1,
            elderly=0,
            gender="No especificado",
            dependents_count=0,
            monthly_income=7500,
            earners=1,
            income_type="variable",
            consumption_level="bajo",
            preferences="economico",
            diet="Flexible",
            purchase_frequency="quincenal",
        ),
        Context(
            name="Hogar premium",
            number_people=3,
            children=1,
            adults=2,
            elderly=0,
            gender="Mixto",
            dependents_count=1,
            monthly_income=36000,
            earners=2,
            income_type="fijo",
            consumption_level="alto",
            preferences="premium",
            diet="Alta en proteína",
            purchase_frequency="semanal",
        ),
    ]

    db.session.add_all(contexts)
    db.session.commit()


def normalize_catalogs():
    """Align old manually entered data with the current catalogs."""
    has_changes = False

    for product in Product.query.all():
        normalized_category = LEGACY_CATEGORY_MAP.get(product.category)
        if normalized_category and normalized_category != product.category:
            product.category = normalized_category
            has_changes = True

        target_prices = {price.store_name: price for price in product.prices}
        for price in list(product.prices):
            normalized_store = LEGACY_STORE_MAP.get(price.store_name)
            if not normalized_store:
                continue

            duplicate = target_prices.get(normalized_store)
            if duplicate and duplicate.id != price.id:
                db.session.delete(price)
            else:
                price.store_name = normalized_store
                target_prices[normalized_store] = price
            has_changes = True

    if has_changes:
        db.session.commit()
