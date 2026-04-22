import re


PRODUCT_CATEGORIES = [
    "Proteínas animales",
    "Cereales y derivados",
    "Leguminosas",
    "Frutas y verduras",
    "Lácteos",
    "Abarrotes",
    "Higiene personal y del hogar",
]

STORE_OPTIONS = ["Walmart", "Bodega Aurrera", "Chedraui"]


def store_field_name(store_name):
    normalized = re.sub(r"[^a-z0-9]+", "_", store_name.lower()).strip("_")
    return f"price_{normalized}"


STORE_FIELDS = [
    {"store": store_name, "field_name": store_field_name(store_name)}
    for store_name in STORE_OPTIONS
]
