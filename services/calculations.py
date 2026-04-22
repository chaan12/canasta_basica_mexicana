import math
from statistics import mean

from catalogs import STORE_OPTIONS


CONSUMPTION_MULTIPLIERS = {
    "bajo": 0.85,
    "medio": 1.0,
    "alto": 1.22,
}

PREFERENCE_MULTIPLIERS = {
    "economico": 0.94,
    "premium": 1.12,
}


def money(value):
    return round(float(value or 0), 2)


def context_factor(context):
    """Calcula un factor de consumo según composición y preferencias."""
    if context is None:
        return 1

    age_weight = (context.children * 0.65) + (context.adults * 1.0) + (context.elderly * 0.85)
    declared_people = max(context.number_people or 1, 1)
    if age_weight <= 0:
        age_weight = declared_people
    elif declared_people > (context.children + context.adults + context.elderly):
        age_weight += declared_people - (context.children + context.adults + context.elderly)

    consumption = CONSUMPTION_MULTIPLIERS.get(context.consumption_level, 1)
    preference = PREFERENCE_MULTIPLIERS.get(context.preferences, 1)
    return max(age_weight * consumption * preference, 0.1)


def choose_product_price(product, store_name=None):
    """Elige el precio de tienda solicitada o el precio más bajo disponible."""
    if store_name:
        store_price = product.price_for_store(store_name)
        if store_price:
            return store_price.price, store_price.store_name, True

    cheapest = product.cheapest_price
    if cheapest:
        return cheapest.price, cheapest.store_name, not bool(store_name)
    return 0, "Sin precio", False


def calculate_basket(products, context=None, store_name=None):
    factor = context_factor(context)
    items = []
    total = 0
    fallback_count = 0

    for product in products:
        price, used_store, exact_store = choose_product_price(product, store_name)
        adjusted_price = price * factor
        total += adjusted_price
        if store_name and not exact_store:
            fallback_count += 1
        items.append(
            {
                "product_name": product.name,
                "price": money(price),
                "adjusted_price": money(adjusted_price),
                "store": used_store,
                "exact_store": exact_store,
            }
        )

    people = max(context.number_people if context else 1, 1)
    income = context.monthly_income if context else 0
    percent_income = (total / income * 100) if income else 0

    return {
        "items": items,
        "total": money(total),
        "cost_per_person": money(total / people),
        "percent_income": money(percent_income),
        "factor": round(factor, 2),
        "fallback_count": fallback_count,
    }


def costs_by_store(products, context=None):
    results = []
    for store in STORE_OPTIONS:
        basket = calculate_basket(products, context=context, store_name=store)
        results.append({"store": store, "total": basket["total"]})
    return sorted(results, key=lambda item: item["total"])


def spending_distribution(products, context=None, store_name=None):
    basket = calculate_basket(products, context=context, store_name=store_name)
    return [
        {"label": item["product_name"], "value": item["adjusted_price"]}
        for item in basket["items"]
        if item["adjusted_price"] > 0
    ]


def category_distribution(products, context=None, store_name=None):
    basket = calculate_basket(products, context=context, store_name=store_name)
    categories = {}
    product_lookup = {product.name: product for product in products}
    for item in basket["items"]:
        product = product_lookup.get(item["product_name"])
        category = product.category if product and product.category else "Sin categoría"
        categories[category] = categories.get(category, 0) + item["adjusted_price"]

    return [
        {"label": category, "value": money(value)}
        for category, value in sorted(categories.items(), key=lambda pair: pair[1], reverse=True)
    ]


def product_price_ranges(products):
    ranges = []
    for product in products:
        prices = [price.price for price in product.prices]
        if not prices:
            continue
        ranges.append(
            {
                "label": product.name,
                "min": money(min(prices)),
                "average": money(sum(prices) / len(prices)),
                "max": money(max(prices)),
            }
        )
    return sorted(ranges, key=lambda item: item["average"], reverse=True)


def simulated_trend(total_cost, months=6):
    labels = ["Mes 1", "Mes 2", "Mes 3", "Mes 4", "Mes 5", "Mes 6", "Mes 7", "Mes 8", "Mes 9", "Mes 10", "Mes 11", "Mes 12"]
    months = max(min(int(months or 6), 12), 3)
    start_index = 12 - months
    selected_labels = labels[start_index:]
    values = []
    base = total_cost * (0.94 if months > 6 else 0.97)
    for index in range(months):
        seasonal = math.sin(index / 1.7) * 0.018
        inflation = 1 + (index * 0.012)
        values.append(money(base * inflation * (1 + seasonal)))
    return {"labels": selected_labels, "values": values}


def gaussian_distribution(total_cost):
    """Simula una distribución de gasto alrededor del costo estimado."""
    if total_cost <= 0:
        return {"labels": [], "values": []}

    labels = []
    values = []
    mean_cost = total_cost
    sigma = max(total_cost * 0.12, 1)
    for offset in range(-5, 6):
        cost = mean_cost + (offset * sigma * 0.55)
        density = math.exp(-0.5 * ((cost - mean_cost) / sigma) ** 2)
        labels.append(f"${round(cost):,}".replace(",", ","))
        values.append(round(density * 100, 2))
    return {"labels": labels, "values": values}


def compare_contexts(contexts, products, store_name=None):
    data = []
    for context in contexts:
        basket = calculate_basket(products, context=context, store_name=store_name)
        data.append(
            {
                "id": context.id,
                "name": context.name,
                "total": basket["total"],
                "per_person": basket["cost_per_person"],
                "percent_income": basket["percent_income"],
                "income": money(context.monthly_income),
                "people": context.number_people,
            }
        )
    return data


def compare_contexts_by_store(contexts, products):
    labels = [context.name for context in contexts]
    datasets = []

    for store_name in STORE_OPTIONS:
        datasets.append(
            {
                "label": store_name,
                "values": [
                    calculate_basket(products, context=context, store_name=store_name)["total"]
                    for context in contexts
                ],
            }
        )

    return {"labels": labels, "datasets": datasets}


def overall_basket(context_comparison, products):
    if context_comparison:
        return {
            "total": money(mean(item["total"] for item in context_comparison)),
            "cost_per_person": money(mean(item["per_person"] for item in context_comparison)),
            "percent_income": money(mean(item["percent_income"] for item in context_comparison)),
            "context_count": len(context_comparison),
            "average_income": money(mean(item["income"] for item in context_comparison)),
            "average_people": round(mean(item["people"] for item in context_comparison), 1),
        }

    basket = calculate_basket(products)
    return {
        "total": basket["total"],
        "cost_per_person": basket["cost_per_person"],
        "percent_income": basket["percent_income"],
        "context_count": 0,
        "average_income": 0,
        "average_people": 0,
    }


def average_costs_by_store(contexts, products):
    results = []
    for store in STORE_OPTIONS:
        if contexts:
            totals = [
                calculate_basket(products, context=context, store_name=store)["total"]
                for context in contexts
            ]
            total = money(mean(totals))
        else:
            total = calculate_basket(products, store_name=store)["total"]
        results.append({"store": store, "total": total})
    return sorted(results, key=lambda item: item["total"])


def most_expensive_product(products):
    candidates = []
    for product in products:
        if product.prices:
            candidates.append((product, product.average_price))
    if not candidates:
        return {"name": "Sin datos", "price": 0}
    product, price = max(candidates, key=lambda item: item[1])
    return {"name": product.name, "price": money(price)}


def cheapest_store(store_costs):
    if not store_costs:
        return {"store": "Sin datos", "total": 0}
    return store_costs[0]


def chart_payload(labels, values):
    return {"labels": labels, "values": values}


def build_dashboard_data(products, contexts, selected_context=None, selected_store=None, time_range="6"):
    context_comparison = compare_contexts(contexts, products)
    basket = overall_basket(context_comparison, products)
    store_costs = average_costs_by_store(contexts, products)
    distribution = spending_distribution(products)
    categories = category_distribution(products)
    price_ranges = product_price_ranges(products)
    store_context_comparison = compare_contexts_by_store(contexts, products)
    trend = simulated_trend(basket["total"], months=time_range)
    gaussian = gaussian_distribution(basket["total"])

    average_store_cost = money(mean([item["total"] for item in store_costs])) if store_costs else 0

    return {
        "basket": basket,
        "store_costs": store_costs,
        "distribution": distribution,
        "categories": categories,
        "price_ranges": price_ranges,
        "context_comparison": context_comparison,
        "trend": trend,
        "gaussian": gaussian,
        "average_store_cost": average_store_cost,
        "cheapest_store": cheapest_store(store_costs),
        "most_expensive_product": most_expensive_product(products),
        "charts": {
            "stores": chart_payload(
                [item["store"] for item in store_costs],
                [item["total"] for item in store_costs],
            ),
            "distribution": chart_payload(
                [item["label"] for item in distribution],
                [item["value"] for item in distribution],
            ),
            "contexts": chart_payload(
                [item["name"] for item in context_comparison],
                [item["total"] for item in context_comparison],
            ),
            "income": chart_payload(
                [item["name"] for item in context_comparison],
                [item["percent_income"] for item in context_comparison],
            ),
            "categories": chart_payload(
                [item["label"] for item in categories],
                [item["value"] for item in categories],
            ),
            "price_ranges": {
                "labels": [item["label"] for item in price_ranges],
                "min": [item["min"] for item in price_ranges],
                "average": [item["average"] for item in price_ranges],
                "max": [item["max"] for item in price_ranges],
            },
            "context_people": chart_payload(
                [item["name"] for item in context_comparison],
                [item["people"] for item in context_comparison],
            ),
            "context_per_person": chart_payload(
                [item["name"] for item in context_comparison],
                [item["per_person"] for item in context_comparison],
            ),
            "context_income": chart_payload(
                [item["name"] for item in context_comparison],
                [item["income"] for item in context_comparison],
            ),
            "store_contexts": store_context_comparison,
        },
    }
