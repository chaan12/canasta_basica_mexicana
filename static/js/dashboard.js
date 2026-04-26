const palette = {
    coral: "#e5484d",
    amber: "#f59e0b",
    green: "#15803d",
    teal: "#0f766e",
    blue: "#2563eb",
    violet: "#7c3aed",
    pink: "#db2777",
    slate: "#334155",
    muted: "#64748b",
    line: "#dbe3ef",
};

const chartColors = [
    palette.teal,
    palette.blue,
    palette.violet,
    palette.pink,
    palette.amber,
    palette.green,
    palette.coral,
];

const dashboardData = window.dashboardData || {};

if (window.Chart) {
    Chart.defaults.font.family = "Inter, system-ui, sans-serif";
    Chart.defaults.color = palette.muted;
    Chart.defaults.responsive = true;
    Chart.defaults.maintainAspectRatio = false;
}

function byId(id) {
    return document.getElementById(id);
}

function products() {
    return dashboardData.products || [];
}

function stores() {
    return dashboardData.store_options || [];
}

function contextComparison() {
    return dashboardData.context_comparison || [];
}

function formatMoney(value) {
    return `$${Number(value || 0).toLocaleString("es-MX", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    })}`;
}

function formatPercent(value) {
    return `${Number(value || 0).toLocaleString("es-MX", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
    })}%`;
}

function priceValues(product) {
    return stores()
        .map((store) => Number(product.prices?.[store] || 0))
        .filter((price) => price > 0);
}

function cheapestPrice(product) {
    const values = priceValues(product);
    return values.length ? Math.min(...values) : 0;
}

function highestPrice(product) {
    const values = priceValues(product);
    return values.length ? Math.max(...values) : 0;
}

function productPrice(product, store) {
    const exactPrice = Number(product.prices?.[store] || 0);
    return exactPrice > 0 ? exactPrice : cheapestPrice(product);
}

function createChart(id, config) {
    const element = byId(id);
    if (!window.Chart || !element) return null;
    return new Chart(element, config);
}

function parsedValue(context) {
    if (typeof context.parsed === "number") {
        return context.parsed;
    }
    if (context.chart?.options?.indexAxis === "y") {
        return context.parsed.x ?? 0;
    }
    return context.parsed.y ?? context.parsed.x ?? 0;
}

function moneyTooltip(context) {
    const prefix = context.dataset.label ? `${context.dataset.label}: ` : "";
    return `${prefix}${formatMoney(parsedValue(context))}`;
}

function percentTooltip(context) {
    const prefix = context.dataset.label ? `${context.dataset.label}: ` : "";
    return `${prefix}${formatPercent(parsedValue(context))}`;
}

function baseBarOptions({ horizontal = false, showLegend = true, formatter = moneyTooltip } = {}) {
    return {
        indexAxis: horizontal ? "y" : "x",
        resizeDelay: 120,
        interaction: { mode: "index", intersect: false },
        plugins: {
            legend: {
                display: showLegend,
                position: "bottom",
                labels: { usePointStyle: true, boxWidth: 8, boxHeight: 8 },
            },
            tooltip: {
                backgroundColor: palette.slate,
                callbacks: { label: formatter },
            },
        },
        scales: {
            x: {
                beginAtZero: true,
                grid: { color: palette.line },
                ticks: {
                    autoSkip: !horizontal,
                    callback: horizontal ? (value) => formatMoney(value) : undefined,
                },
            },
            y: {
                beginAtZero: true,
                grid: { color: palette.line },
                ticks: {
                    callback: !horizontal ? (value) => formatMoney(value) : undefined,
                },
            },
        },
    };
}

function initIncomeBasketChart() {
    const chart = dashboardData.charts?.context_income_basket || {};
    createChart("incomeBasketChart", {
        type: "bar",
        data: {
            labels: chart.labels || [],
            datasets: [
                {
                    label: "Ingreso quincenal",
                    data: chart.income || [],
                    backgroundColor: "rgba(37, 99, 235, 0.72)",
                    borderRadius: 8,
                },
                {
                    label: "Canasta quincenal",
                    data: chart.basket || [],
                    backgroundColor: "rgba(15, 118, 110, 0.72)",
                    borderRadius: 8,
                },
            ],
        },
        options: baseBarOptions({ showLegend: true }),
    });
}

function initPressureChart() {
    const chart = dashboardData.charts?.context_pressure || {};
    createChart("pressureByContextChart", {
        type: "bar",
        data: {
            labels: chart.labels || [],
            datasets: [{
                label: "% del ingreso",
                data: chart.values || [],
                backgroundColor: (chart.values || []).map((value) => {
                    if (value >= 50) return palette.coral;
                    if (value >= 30) return palette.amber;
                    return palette.green;
                }),
                borderRadius: 8,
            }],
        },
        options: {
            ...baseBarOptions({ showLegend: false, formatter: percentTooltip }),
            scales: {
                x: {
                    grid: { color: palette.line },
                    ticks: { maxRotation: 0, autoSkip: true },
                },
                y: {
                    beginAtZero: true,
                    grid: { color: palette.line },
                    ticks: { callback: (value) => formatPercent(value) },
                },
            },
        },
    });
}

function initPerPersonChart() {
    const chart = dashboardData.charts?.context_per_person || {};
    createChart("perPersonChart", {
        type: "bar",
        data: {
            labels: chart.labels || [],
            datasets: [
                {
                    label: "Ingreso por integrante",
                    data: chart.income || [],
                    backgroundColor: "rgba(37, 99, 235, 0.72)",
                    borderRadius: 8,
                },
                {
                    label: "Canasta por integrante",
                    data: chart.basket || [],
                    backgroundColor: "rgba(245, 158, 11, 0.74)",
                    borderRadius: 8,
                },
            ],
        },
        options: baseBarOptions({ showLegend: true }),
    });
}

function initEarnersScatterChart() {
    createChart("earnersScatterChart", {
        type: "bubble",
        data: {
            datasets: [{
                label: "Contextos",
                data: dashboardData.charts?.context_earners_scatter || [],
                backgroundColor: "rgba(124, 58, 237, 0.62)",
                borderColor: palette.violet,
                borderWidth: 2,
            }],
        },
        options: {
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: palette.slate,
                    callbacks: {
                        label: (context) => {
                            const point = context.raw;
                            return [
                                `${point.label}: ${point.x} integrantes, ${point.earners} perceptores`,
                                `Canasta: ${formatMoney(point.basket)}`,
                                `Ingreso quincenal: ${formatMoney(point.income)}`,
                                `Presión: ${formatPercent(point.y)}`,
                            ];
                        },
                    },
                },
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { color: palette.line },
                    title: { display: true, text: "Integrantes del hogar" },
                    ticks: { precision: 0 },
                },
                y: {
                    beginAtZero: true,
                    grid: { color: palette.line },
                    title: { display: true, text: "% del ingreso quincenal" },
                    ticks: { callback: (value) => formatPercent(value) },
                },
            },
        },
    });
}

function initPriceRangeChart() {
    const sortedProducts = [...products()].sort((left, right) => Number(right.price_variance || 0) - Number(left.price_variance || 0));
    createChart("priceRangeChart", {
        type: "bar",
        data: {
            labels: sortedProducts.map((product) => product.name),
            datasets: [
                {
                    label: "Más barato",
                    data: sortedProducts.map((product) => cheapestPrice(product)),
                    backgroundColor: "rgba(21, 128, 61, 0.68)",
                    borderColor: palette.green,
                    borderWidth: 1,
                    borderRadius: 6,
                },
                {
                    label: "Más caro",
                    data: sortedProducts.map((product) => highestPrice(product)),
                    backgroundColor: "rgba(229, 72, 77, 0.68)",
                    borderColor: palette.coral,
                    borderWidth: 1,
                    borderRadius: 6,
                },
            ],
        },
        options: baseBarOptions({ horizontal: true, showLegend: true }),
    });
}

function initAllProductsComparisonChart() {
    createChart("allProductsComparisonChart", {
        type: "bar",
        data: {
            labels: products().map((product) => product.name),
            datasets: stores().map((store, index) => ({
                label: store,
                data: products().map((product) => productPrice(product, store)),
                backgroundColor: chartColors[index % chartColors.length],
                borderRadius: 5,
            })),
        },
        options: baseBarOptions({ horizontal: true, showLegend: true }),
    });
}

function updateVariationList() {
    const container = byId("variationList");
    if (!container) return;

    const items = [...products()]
        .sort((left, right) => Number(right.price_variance || 0) - Number(left.price_variance || 0))
        .slice(0, 6);

    container.innerHTML = items.map((product, index) => `
        <div class="variation-item">
            <span>${index + 1}</span>
            <div>
                <strong>${product.name}</strong>
                <small>${product.cheapest_store}: ${formatMoney(product.cheapest_price)} · ${product.highest_store}: ${formatMoney(product.highest_price)}</small>
            </div>
            <b>${formatMoney(product.price_variance)}</b>
        </div>
    `).join("");
}

document.addEventListener("DOMContentLoaded", () => {
    initIncomeBasketChart();
    initPressureChart();
    initPerPersonChart();
    initEarnersScatterChart();
    initPriceRangeChart();
    initAllProductsComparisonChart();
    updateVariationList();
});
