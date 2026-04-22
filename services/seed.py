from models import Context, Product, StorePrice, db


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


def seed_database():
    """Agrega datos iniciales para que el tablero tenga información al arrancar."""
    if Product.query.first() or Context.query.first():
        return

    products = [
        {
            "name": "Leche",
            "category": "Lácteos",
            "quantity_value": 1,
            "quantity_unit": "l",
            "prices": {"Walmart": 28, "Bodega Aurrera": 30, "Chedraui": 25},
        },
        {
            "name": "Tortilla de maíz",
            "category": "Cereales y derivados",
            "quantity_value": 1,
            "quantity_unit": "kg",
            "prices": {"Walmart": 24, "Bodega Aurrera": 23, "Chedraui": 22},
        },
        {
            "name": "Huevo",
            "category": "Proteínas animales",
            "quantity_value": 1,
            "quantity_unit": "kg",
            "prices": {"Walmart": 48, "Bodega Aurrera": 52, "Chedraui": 46},
        },
        {
            "name": "Frijol",
            "category": "Leguminosas",
            "quantity_value": 1,
            "quantity_unit": "kg",
            "prices": {"Walmart": 42, "Bodega Aurrera": 39, "Chedraui": 38},
        },
        {
            "name": "Arroz",
            "category": "Cereales y derivados",
            "quantity_value": 1,
            "quantity_unit": "kg",
            "prices": {"Walmart": 31, "Bodega Aurrera": 29, "Chedraui": 30},
        },
        {
            "name": "Pollo",
            "category": "Proteínas animales",
            "quantity_value": 1,
            "quantity_unit": "kg",
            "prices": {"Walmart": 98, "Bodega Aurrera": 95, "Chedraui": 90},
        },
        {
            "name": "Jitomate",
            "category": "Frutas y verduras",
            "quantity_value": 1,
            "quantity_unit": "kg",
            "prices": {"Walmart": 34, "Bodega Aurrera": 36, "Chedraui": 28},
        },
        {
            "name": "Aceite vegetal",
            "category": "Abarrotes",
            "quantity_value": 1,
            "quantity_unit": "l",
            "prices": {"Walmart": 48, "Bodega Aurrera": 51, "Chedraui": 49},
        },
    ]

    for item in products:
        product = Product(
            name=item["name"],
            category=item["category"],
            quantity_value=item["quantity_value"],
            quantity_unit=item["quantity_unit"],
        )
        for store, price in item["prices"].items():
            product.prices.append(StorePrice(store_name=store, price=price))
        db.session.add(product)

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
    """Alinea datos heredados con los catálogos fijos actuales."""
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
