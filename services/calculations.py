from statistics import mean

from catalogs import STORE_OPTIONS
from services.catalog_importer import (
    BASKET_BIWEEKLY_MULTIPLIER,
    BASKET_REFERENCE_PEOPLE,
)


def money(value):
    return round(float(value or 0), 2)


def safe_people_count(value):
    return max(int(value or 1), 1)


def product_price_values(product):
    return [price.price for price in product.prices if price.price is not None and price.price > 0]


def choose_product_price(product, store_name=None):
    if store_name:
        store_price = product.price_for_store(store_name)
        if store_price:
            return store_price.price, store_price.store_name, True

    cheapest = product.cheapest_price
    if cheapest:
        return cheapest.price, cheapest.store_name, not bool(store_name)
    return 0, "Sin precio", False


def context_consumption_units(context):
    if context is None:
        return 1

    children = max(context.children or 0, 0)
    declared_people = safe_people_count(context.number_people)
    adults = max(declared_people - children, 0)
    return max((adults * 1.0) + (children * 0.65), 0.1)


def biweekly_scale_factor(people_count, children_count=0):
    people = safe_people_count(people_count)
    children = min(max(int(children_count or 0), 0), people)
    adults = people - children
    consumption_units = (adults * 1.0) + (children * 0.65)
    return money((consumption_units / BASKET_REFERENCE_PEOPLE) * BASKET_BIWEEKLY_MULTIPLIER)


def calculate_basket(products, context=None, store_name=None, scale_factor=None):
    if scale_factor is None:
        people = safe_people_count(context.number_people) if context else BASKET_REFERENCE_PEOPLE
        children = max(context.children or 0, 0) if context else 0
        scale_factor = biweekly_scale_factor(people, children)

    items = []
    total = 0
    fallback_count = 0

    for product in products:
        price, used_store, exact_store = choose_product_price(product, store_name)
        adjusted_price = price * scale_factor
        total += adjusted_price
        if store_name and not exact_store:
            fallback_count += 1
        items.append(
            {
                "product_name": product.name,
                "presentation": product.display_quantity,
                "base_price": money(price),
                "adjusted_price": money(adjusted_price),
                "store": used_store,
                "exact_store": exact_store,
            }
        )

    people = safe_people_count(context.number_people) if context else BASKET_REFERENCE_PEOPLE
    income = context.monthly_income if context else 0
    percent_income = (total / income * 100) if income else 0

    return {
        "items": items,
        "total": money(total),
        "cost_per_person": money(total / people),
        "percent_income": money(percent_income),
        "scale_factor": money(scale_factor),
        "fallback_count": fallback_count,
    }


def costs_by_store(products, scale_factor=1):
    results = []
    for store in STORE_OPTIONS:
        basket = calculate_basket(products, store_name=store, scale_factor=scale_factor)
        results.append({"store": store, "total": basket["total"]})
    return sorted(results, key=lambda item: item["total"])


def product_payload(product):
    prices = {price.store_name: money(price.price) for price in product.prices}
    values = list(prices.values())
    cheapest_store = min(prices, key=prices.get) if prices else "Sin datos"
    highest_store = max(prices, key=prices.get) if prices else "Sin datos"
    return {
        "id": product.id,
        "name": product.name,
        "category": product.category or "Sin categoría",
        "presentation": product.display_quantity,
        "quantity_value": money(product.quantity_value),
        "quantity_unit": product.quantity_unit,
        "prices": prices,
        "cheapest_store": cheapest_store,
        "cheapest_price": money(prices.get(cheapest_store, 0)),
        "highest_store": highest_store,
        "highest_price": money(prices.get(highest_store, 0)),
        "average_market_price": money(mean(values)) if values else 0,
        "price_variance": money(max(values) - min(values)) if values else 0,
    }


def product_price_ranges(products):
    ranges = []
    for product in products:
        values = product_price_values(product)
        if not values:
            continue
        ranges.append(
            {
                "label": product.name,
                "min": money(min(values)),
                "average": money(mean(values)),
                "max": money(max(values)),
                "variance": money(max(values) - min(values)),
            }
        )
    return sorted(ranges, key=lambda item: item["variance"], reverse=True)


def category_distribution(products, store_name=None):
    categories = {}
    for product in products:
        price, _, _ = choose_product_price(product, store_name)
        category = product.category or "Sin categoría"
        categories[category] = categories.get(category, 0) + price

    return [
        {"label": category, "value": money(value)}
        for category, value in sorted(categories.items(), key=lambda pair: pair[1], reverse=True)
    ]


def compare_contexts(contexts, products, store_name=None):
    data = []
    for context in contexts:
        scale_factor = biweekly_scale_factor(context.number_people, context.children)
        store_totals = costs_by_store(products, scale_factor=scale_factor)
        selected_total = None
        if store_name:
            selected_total = next((item for item in store_totals if item["store"] == store_name), None)
        cheapest_total = store_totals[0] if store_totals else {"store": "Sin datos", "total": 0}
        basket_total = selected_total or cheapest_total
        people = safe_people_count(context.number_people)
        earners = max(int(context.earners or 1), 1)
        biweekly_income = money((context.monthly_income or 0) / 2)
        percent_income = money((basket_total["total"] / biweekly_income * 100) if biweekly_income else 0)
        data.append(
            {
                "id": context.id,
                "name": context.name,
                "total": basket_total["total"],
                "store": basket_total["store"],
                "per_person": money(basket_total["total"] / people),
                "per_earner": money(basket_total["total"] / earners),
                "percent_income": percent_income,
                "income": money(context.monthly_income),
                "biweekly_income": biweekly_income,
                "income_per_person": money(biweekly_income / people) if people else 0,
                "income_per_earner": money(biweekly_income / earners) if earners else 0,
                "people": people,
                "children": max(context.children or 0, 0),
                "earners": earners,
                "dependents": max(people - earners, 0),
                "scale_factor": scale_factor,
            }
        )
    return data


def summarize_contexts(context_comparison):
    if not context_comparison:
        return {
            "average_basket": 0,
            "average_income_pressure": 0,
            "highest_pressure_context": "Sin contextos",
            "highest_pressure": 0,
            "one_earner_count": 0,
        }

    highest_pressure = max(context_comparison, key=lambda item: item["percent_income"])
    return {
        "average_basket": money(mean(item["total"] for item in context_comparison)),
        "average_income_pressure": money(mean(item["percent_income"] for item in context_comparison)),
        "highest_pressure_context": highest_pressure["name"],
        "highest_pressure": highest_pressure["percent_income"],
        "one_earner_count": sum(1 for item in context_comparison if item["earners"] == 1),
    }


def cheapest_store(store_costs):
    if not store_costs:
        return {"store": "Sin datos", "total": 0}
    return store_costs[0]


def highest_variation_products(products, limit=5):
    return product_price_ranges(products)[:limit]


def chart_payload(labels, values):
    return {"labels": labels, "values": values}


def build_dashboard_data(products, contexts, selected_context=None, selected_store=None, time_range="6"):
    serialized_products = [product_payload(product) for product in products]
    weekly_store_costs = costs_by_store(products, scale_factor=1)
    biweekly_family_store_costs = costs_by_store(products, scale_factor=BASKET_BIWEEKLY_MULTIPLIER)
    context_comparison = compare_contexts(contexts, products)
    context_summary = summarize_contexts(context_comparison)
    ranges = product_price_ranges(products)
    categories = category_distribution(products)
    average_weekly_cost = money(mean([item["total"] for item in weekly_store_costs])) if weekly_store_costs else 0
    average_biweekly_family_cost = money(average_weekly_cost * BASKET_BIWEEKLY_MULTIPLIER)

    return {
        "reference": {
            "people": BASKET_REFERENCE_PEOPLE,
            "period": "Semanal",
            "biweekly_multiplier": BASKET_BIWEEKLY_MULTIPLIER,
        },
        "store_options": STORE_OPTIONS,
        "products": serialized_products,
        "basket": {
            "product_count": len(products),
            "average_weekly_cost": average_weekly_cost,
            "average_biweekly_family_cost": average_biweekly_family_cost,
            "context_count": len(contexts),
        },
        "store_costs": weekly_store_costs,
        "biweekly_family_store_costs": biweekly_family_store_costs,
        "cheapest_store": cheapest_store(weekly_store_costs),
        "top_variation_products": highest_variation_products(products),
        "categories": categories,
        "context_comparison": context_comparison,
        "context_summary": context_summary,
        "charts": {
            "store_totals": chart_payload(
                [item["store"] for item in weekly_store_costs],
                [item["total"] for item in weekly_store_costs],
            ),
            "biweekly_family_store_totals": chart_payload(
                [item["store"] for item in biweekly_family_store_costs],
                [item["total"] for item in biweekly_family_store_costs],
            ),
            "categories": chart_payload(
                [item["label"] for item in categories],
                [item["value"] for item in categories],
            ),
            "price_ranges": {
                "labels": [item["label"] for item in ranges],
                "min": [item["min"] for item in ranges],
                "average": [item["average"] for item in ranges],
                "max": [item["max"] for item in ranges],
                "variance": [item["variance"] for item in ranges],
            },
            "context_income_basket": {
                "labels": [item["name"] for item in context_comparison],
                "income": [item["biweekly_income"] for item in context_comparison],
                "basket": [item["total"] for item in context_comparison],
            },
            "context_pressure": {
                "labels": [item["name"] for item in context_comparison],
                "values": [item["percent_income"] for item in context_comparison],
                "people": [item["people"] for item in context_comparison],
                "earners": [item["earners"] for item in context_comparison],
            },
            "context_per_person": {
                "labels": [item["name"] for item in context_comparison],
                "basket": [item["per_person"] for item in context_comparison],
                "income": [item["income_per_person"] for item in context_comparison],
            },
            "context_earners_scatter": [
                {
                    "label": item["name"],
                    "x": item["people"],
                    "y": item["percent_income"],
                    "r": min(max(item["earners"] * 5, 5), 18),
                    "earners": item["earners"],
                    "basket": item["total"],
                    "income": item["biweekly_income"],
                }
                for item in context_comparison
            ],
        },
    }
