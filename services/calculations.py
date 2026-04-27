from statistics import mean

from catalogs import STORE_OPTIONS
from services.catalog_importer import (
    BASKET_BIWEEKLY_MULTIPLIER,
    BASKET_REFERENCE_PEOPLE,
)


ADULT_CONSUMPTION_WEIGHT = 1.0
CHILD_CONSUMPTION_WEIGHT = 0.65
CONSUMPTION_LEVEL_MULTIPLIERS = {
    "bajo": 0.9,
    "medio": 1.0,
    "alto": 1.12,
}
PREFERENCE_MULTIPLIERS = {
    "economico": 1.0,
    "premium": 1.08,
}
COMMON_HOUSEHOLD_EXPENSES = [
    {
        "key": "housing",
        "label": "Vivienda",
        "expense_type": "fixed",
        "income_rate": 0.22,
        "per_person_floor": 700,
    },
    {
        "key": "utilities",
        "label": "Servicios: luz, agua y gas",
        "expense_type": "fixed",
        "income_rate": 0.07,
        "base_floor": 360,
        "per_person_floor": 90,
    },
    {
        "key": "transport",
        "label": "Transporte",
        "expense_type": "fixed",
        "income_rate": 0.10,
        "per_adult_floor": 420,
        "per_child_floor": 220,
    },
    {
        "key": "communication",
        "label": "Comunicación e internet",
        "expense_type": "fixed",
        "income_rate": 0.05,
        "base_floor": 260,
        "per_person_floor": 90,
    },
    {
        "key": "education",
        "label": "Educación y cuidado",
        "expense_type": "fixed",
        "income_rate": 0.10,
        "per_child_floor": 650,
        "requires_children": True,
    },
    {
        "key": "health",
        "label": "Salud",
        "expense_type": "variable",
        "income_rate": 0.03,
        "per_person_floor": 120,
    },
    {
        "key": "cleaning",
        "label": "Higiene y limpieza",
        "expense_type": "variable",
        "income_rate": 0.04,
        "per_person_floor": 110,
    },
    {
        "key": "other_home",
        "label": "Otros gastos del hogar",
        "expense_type": "variable",
        "income_rate": 0.06,
        "per_person_floor": 180,
    },
]


def money(value):
    return round(float(value or 0), 2)


def safe_count(value, default=0, minimum=0):
    try:
        numeric_value = int(value)
    except (TypeError, ValueError):
        numeric_value = default
    return max(numeric_value, minimum)


def safe_people_count(value):
    return safe_count(value, default=1, minimum=1)


def household_counts(context):
    if context is None:
        return BASKET_REFERENCE_PEOPLE, 0

    children = safe_count(getattr(context, "children", 0), default=0, minimum=0)
    adults = safe_count(getattr(context, "adults", 0), default=0, minimum=0)
    if adults <= 0:
        adults = max(safe_people_count(getattr(context, "number_people", 1)) - children, 1)
    return adults, children


def household_people_count(adults_count, children_count):
    return max(safe_count(adults_count, default=1, minimum=0) + safe_count(children_count, default=0, minimum=0), 1)


def household_type_label(adults_count, children_count):
    if safe_count(children_count, default=0, minimum=0) > 0:
        return "Familia"
    if safe_count(adults_count, default=1, minimum=1) > 1:
        return "Pareja"
    return "Vive solo"


def household_consumption_units(adults_count, children_count):
    adults = safe_count(adults_count, default=1, minimum=0)
    children = safe_count(children_count, default=0, minimum=0)
    return max((adults * ADULT_CONSUMPTION_WEIGHT) + (children * CHILD_CONSUMPTION_WEIGHT), 0.1)


def common_household_expenses(monthly_income, adults_count, children_count):
    people = household_people_count(adults_count, children_count)
    adults = safe_count(adults_count, default=1, minimum=0)
    children = safe_count(children_count, default=0, minimum=0)
    expenses = []

    for rule in COMMON_HOUSEHOLD_EXPENSES:
        if rule.get("requires_children") and children <= 0:
            continue

        floor_amount = (
            rule.get("base_floor", 0)
            + (rule.get("per_person_floor", 0) * people)
            + (rule.get("per_adult_floor", 0) * adults)
            + (rule.get("per_child_floor", 0) * children)
        )
        income_amount = money(monthly_income) * rule.get("income_rate", 0)
        amount = money(max(income_amount, floor_amount))
        if amount <= 0:
            continue

        expenses.append(
            {
                "key": rule["key"],
                "label": rule["label"],
                "type": rule["expense_type"],
                "value": amount,
            }
        )

    return expenses


def financial_health(monthly_income, total_expenses, remaining):
    income = money(monthly_income)
    remaining_ratio = (remaining / income) if income else 0
    score = money(max(0, min(100, remaining_ratio * 100))) if income else 0

    if remaining < 0 or (income <= 0 and total_expenses > 0) or (income > 0 and remaining_ratio < 0.05):
        return {
            "state": "red",
            "label": "En riesgo",
            "score": score,
            "message": "Los gastos consumen casi todo el ingreso mensual o generan déficit.",
        }
    if remaining_ratio < 0.15:
        return {
            "state": "yellow",
            "label": "Ajustado",
            "score": score,
            "message": "El contexto tiene poco margen para imprevistos.",
        }
    return {
        "state": "green",
        "label": "Saludable",
        "score": score,
        "message": "El contexto mantiene saldo disponible después de cubrir gastos comunes.",
    }


def context_consumption_multiplier(context):
    if context is None:
        return 1
    consumption_level = (context.consumption_level or "medio").strip().lower()
    preferences = (context.preferences or "economico").strip().lower()
    return CONSUMPTION_LEVEL_MULTIPLIERS.get(consumption_level, 1) * PREFERENCE_MULTIPLIERS.get(preferences, 1)


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
    adults, children = household_counts(context)
    return household_consumption_units(adults, children)


def biweekly_scale_factor(adults_count=1, children_count=0, consumption_multiplier=1):
    consumption_units = household_consumption_units(adults_count, children_count)
    return money((consumption_units / BASKET_REFERENCE_PEOPLE) * BASKET_BIWEEKLY_MULTIPLIER * consumption_multiplier)


def calculate_basket(products, context=None, store_name=None, scale_factor=None):
    if scale_factor is None:
        adults, children = household_counts(context)
        scale_factor = biweekly_scale_factor(adults, children, context_consumption_multiplier(context))

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

    adults, children = household_counts(context)
    people = household_people_count(adults, children)
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
        adults, children = household_counts(context)
        scale_factor = biweekly_scale_factor(adults, children, context_consumption_multiplier(context))
        store_totals = costs_by_store(products, scale_factor=scale_factor)
        selected_total = None
        if store_name:
            selected_total = next((item for item in store_totals if item["store"] == store_name), None)
        cheapest_total = store_totals[0] if store_totals else {"store": "Sin datos", "total": 0}
        basket_total = selected_total or cheapest_total
        people = household_people_count(adults, children)
        earners = min(max(int(context.earners or 1), 1), max(adults, 1))
        monthly_income = money(context.monthly_income)
        biweekly_income = money(monthly_income / 2)
        percent_income = money((basket_total["total"] / biweekly_income * 100) if biweekly_income else 0)
        basket_monthly = money(basket_total["total"] * 2)
        common_expenses = common_household_expenses(monthly_income, adults, children)
        expense_distribution = [
            {
                "key": "basic_basket",
                "label": "Canasta básica",
                "type": "fixed",
                "value": basket_monthly,
            },
            *common_expenses,
        ]
        fixed_expenses = money(
            sum(item["value"] for item in expense_distribution if item["type"] == "fixed")
        )
        variable_expenses = money(
            sum(item["value"] for item in expense_distribution if item["type"] == "variable")
        )
        total_expenses = money(fixed_expenses + variable_expenses)
        remaining = money(monthly_income - total_expenses)
        units = household_consumption_units(adults, children)
        adult_share = (adults * ADULT_CONSUMPTION_WEIGHT) / units
        children_share = (children * CHILD_CONSUMPTION_WEIGHT) / units
        health = financial_health(monthly_income, total_expenses, remaining)
        data.append(
            {
                "id": context.id,
                "name": context.name,
                "household_type": household_type_label(adults, children),
                "total": basket_total["total"],
                "store": basket_total["store"],
                "per_person": money(basket_total["total"] / people),
                "per_earner": money(basket_total["total"] / earners),
                "percent_income": percent_income,
                "income": monthly_income,
                "biweekly_income": biweekly_income,
                "income_per_person": money(biweekly_income / people) if people else 0,
                "income_per_earner": money(biweekly_income / earners) if earners else 0,
                "people": people,
                "adults": adults,
                "children": children,
                "earners": earners,
                "dependents": max(people - earners, 0),
                "scale_factor": scale_factor,
                "monthly_scale_factor": money(scale_factor * 2),
                "basket_monthly": basket_monthly,
                "basket_monthly_per_person": money(basket_monthly / people),
                "adult_basket_monthly": money(basket_monthly * adult_share),
                "children_basket_monthly": money(basket_monthly * children_share),
                "common_expenses": common_expenses,
                "expense_distribution": expense_distribution,
                "fixed_expenses": fixed_expenses,
                "variable_expenses": variable_expenses,
                "total_expenses": total_expenses,
                "remaining": remaining,
                "remaining_percent": money((remaining / monthly_income * 100) if monthly_income else 0),
                "health": health,
                "store_monthly_costs": [
                    {"store": item["store"], "total": money(item["total"] * 2)}
                    for item in store_totals
                ],
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


def build_dashboard_data(products, contexts, time_range="6", store_name=None):
    serialized_products = [product_payload(product) for product in products]
    weekly_store_costs = costs_by_store(products, scale_factor=1)
    biweekly_family_store_costs = costs_by_store(products, scale_factor=BASKET_BIWEEKLY_MULTIPLIER)
    context_comparison = compare_contexts(contexts, products, store_name=store_name)
    context_summary = summarize_contexts(context_comparison)
    ranges = product_price_ranges(products)
    categories = category_distribution(products, store_name=store_name)
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
        "active_store": store_name,
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
            "context_monthly_budget": {
                "labels": [item["name"] for item in context_comparison],
                "income": [item["income"] for item in context_comparison],
                "fixed": [item["fixed_expenses"] for item in context_comparison],
                "variable": [item["variable_expenses"] for item in context_comparison],
                "remaining": [item["remaining"] for item in context_comparison],
            },
            "context_health": {
                "labels": [item["name"] for item in context_comparison],
                "scores": [item["health"]["score"] for item in context_comparison],
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
