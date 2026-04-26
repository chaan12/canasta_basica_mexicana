import json
import os
import re
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "data" / "basic_basket.json"
DEFAULT_EXCEL_NAME = "Hoja de cálculo sin título.xlsx"
BASKET_REFERENCE_PEOPLE = 4
BASKET_REFERENCE_PERIOD = "weekly"
BASKET_BIWEEKLY_MULTIPLIER = 2


def normalize_key(value):
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", ascii_value.lower()).strip("_")


def money(value):
    return round(float(value or 0), 2)


def default_excel_candidates():
    candidates = []
    configured_path = os.environ.get("BASKET_EXCEL_PATH")
    if configured_path:
        candidates.append(Path(configured_path).expanduser())
    candidates.append(Path.home() / "Downloads" / DEFAULT_EXCEL_NAME)
    return candidates


def _namespace(tag):
    match = re.match(r"\{(.+)\}", tag)
    return {"x": match.group(1)} if match else {}


def _column_index(reference):
    letters = re.match(r"([A-Z]+)", reference or "")
    if not letters:
        return 0
    index = 0
    for char in letters.group(1):
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index - 1


def _load_shared_strings(archive):
    try:
        with archive.open("xl/sharedStrings.xml") as file:
            root = ElementTree.parse(file).getroot()
    except KeyError:
        return []

    ns = _namespace(root.tag)
    values = []
    for item in root.findall("x:si", ns):
        texts = [node.text or "" for node in item.findall(".//x:t", ns)]
        values.append("".join(texts))
    return values


def _cell_value(cell, shared_strings, ns):
    cell_type = cell.attrib.get("t")
    value_node = cell.find("x:v", ns)

    if cell_type == "inlineStr":
        texts = [node.text or "" for node in cell.findall(".//x:t", ns)]
        return "".join(texts).strip()

    if value_node is None or value_node.text is None:
        return None

    raw_value = value_node.text
    if cell_type == "s":
        index = int(raw_value)
        return shared_strings[index].strip() if index < len(shared_strings) else ""

    try:
        numeric = float(raw_value)
        return int(numeric) if numeric.is_integer() else numeric
    except ValueError:
        return raw_value.strip()


def read_first_sheet_rows(excel_path):
    with zipfile.ZipFile(excel_path) as archive:
        shared_strings = _load_shared_strings(archive)
        with archive.open("xl/worksheets/sheet1.xml") as file:
            root = ElementTree.parse(file).getroot()

    ns = _namespace(root.tag)
    rows = []
    for row_node in root.findall(".//x:sheetData/x:row", ns):
        values = []
        for cell in row_node.findall("x:c", ns):
            index = _column_index(cell.attrib.get("r", ""))
            while len(values) <= index:
                values.append(None)
            values[index] = _cell_value(cell, shared_strings, ns)
        rows.append(values)
    return rows


def normalize_unit(unit):
    unit = normalize_key(unit)
    if unit in {"kilogramo", "kilogramos", "kg"}:
        return "kg"
    if unit in {"gramo", "gramos", "g"}:
        return "g"
    if unit in {"litro", "litros", "l"}:
        return "l"
    if unit in {"mililitro", "mililitros", "ml"}:
        return "ml"
    if unit in {"pieza", "piezas", "pza", "pzas"}:
        return "pza"
    return unit or "pza"


def parse_presentation(presentation):
    text = str(presentation or "").lower().replace(",", ".")
    compound = re.search(
        r"(\d+(?:\.\d+)?)\s+\w+\s+de\s+(\d+(?:\.\d+)?)\s*(kg|g|ml|l|litro|litros|pieza|piezas)",
        text,
    )
    if compound:
        count = float(compound.group(1))
        amount = float(compound.group(2))
        return count * amount, normalize_unit(compound.group(3))

    simple = re.search(r"(\d+(?:\.\d+)?)\s*(kg|g|ml|l|litro|litros|pieza|piezas)", text)
    if simple:
        return float(simple.group(1)), normalize_unit(simple.group(2))

    return 1.0, "pza"


def infer_category(product_name):
    key = normalize_key(product_name)
    category_rules = [
        (("atun", "sardina", "carne", "pollo", "huevo", "cerdo", "res"), "Proteínas animales"),
        (("arroz", "tortilla", "pan", "pasta"), "Cereales y derivados"),
        (("frijol",), "Leguminosas"),
        (
            ("cebolla", "chile", "jitomate", "limon", "manzana", "platano", "papa", "zanahoria"),
            "Frutas y verduras",
        ),
        (("leche",), "Lácteos"),
        (("jabon", "papel"), "Higiene personal y del hogar"),
        (("aceite", "azucar"), "Abarrotes"),
    ]
    for keywords, category in category_rules:
        if any(keyword in key for keyword in keywords):
            return category
    return "Abarrotes"


def split_product_label(label):
    text = str(label or "").strip()
    match = re.match(r"^(.*?)\s*\((.*?)\)\s*$", text)
    if not match:
        return text, ""
    return match.group(1).strip(), match.group(2).strip()


def build_product_record(label, stores, price_values):
    name, presentation = split_product_label(label)
    quantity_value, quantity_unit = parse_presentation(presentation)
    prices = {
        store: money(price)
        for store, price in zip(stores, price_values)
        if isinstance(price, (int, float)) and float(price) > 0
    }
    price_list = list(prices.values())
    cheapest_store = min(prices, key=prices.get) if prices else ""
    most_expensive_store = max(prices, key=prices.get) if prices else ""
    return {
        "source_key": normalize_key(name),
        "name": name,
        "presentation": presentation,
        "quantity_value": quantity_value,
        "quantity_unit": quantity_unit,
        "category": infer_category(name),
        "prices": prices,
        "cheapest_supermarket": cheapest_store,
        "most_expensive_supermarket": most_expensive_store,
        "average_market_price": money(sum(price_list) / len(price_list)) if price_list else 0,
        "price_variance": money(max(price_list) - min(price_list)) if price_list else 0,
    }


def parse_excel_catalog(excel_path):
    rows = read_first_sheet_rows(excel_path)
    store_row_index = None
    stores = []

    for index, row in enumerate(rows[:10]):
        candidate_stores = [cell for cell in row[1:] if isinstance(cell, str) and cell.strip()]
        if len(candidate_stores) >= 3:
            store_row_index = index
            stores = [cell.strip() for cell in candidate_stores]
            break

    if store_row_index is None:
        raise ValueError("No supermarket header row was found in the spreadsheet.")

    products = []
    for row in rows[store_row_index + 1 :]:
        if not row or not row[0]:
            continue
        label = str(row[0]).strip()
        if normalize_key(label) == "total":
            break
        products.append(build_product_record(label, stores, row[1 : 1 + len(stores)]))

    return {
        "source": {
            "file_name": Path(excel_path).name,
            "worksheet": "Hoja 1",
        },
        "basket_reference": {
            "people": BASKET_REFERENCE_PEOPLE,
            "period": BASKET_REFERENCE_PERIOD,
            "biweekly_multiplier": BASKET_BIWEEKLY_MULTIPLIER,
        },
        "stores": stores,
        "products": products,
    }


def save_catalog(catalog, output_path=DEFAULT_CATALOG_PATH):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path


def load_basket_catalog(catalog_path=DEFAULT_CATALOG_PATH):
    configured_path = os.environ.get("BASKET_EXCEL_PATH")
    if configured_path and Path(configured_path).expanduser().exists():
        return parse_excel_catalog(Path(configured_path).expanduser())

    catalog_path = Path(catalog_path)
    if catalog_path.exists():
        return json.loads(catalog_path.read_text(encoding="utf-8"))

    for excel_path in default_excel_candidates():
        if excel_path.exists():
            return parse_excel_catalog(excel_path)

    return {
        "basket_reference": {
            "people": BASKET_REFERENCE_PEOPLE,
            "period": BASKET_REFERENCE_PERIOD,
            "biweekly_multiplier": BASKET_BIWEEKLY_MULTIPLIER,
        },
        "stores": ["Walmart", "Chedraui", "Bodega Aurrera"],
        "products": [],
    }


def load_store_names():
    catalog = load_basket_catalog()
    stores = catalog.get("stores") or []
    return stores if len(stores) >= 3 else ["Walmart", "Chedraui", "Bodega Aurrera"]
