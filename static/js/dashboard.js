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
const contextCharts = {};

if (window.Chart) {
    Chart.defaults.font.family = "Inter, system-ui, sans-serif";
    Chart.defaults.color = palette.muted;
    Chart.defaults.responsive = true;
    Chart.defaults.maintainAspectRatio = false;
}

function byId(id) {
    return document.getElementById(id);
}

function getSearchParam(key) {
    try {
        return new URL(window.location.href).searchParams.get(key);
    } catch (error) {
        return null;
    }
}

function setSearchParam(key, value) {
    try {
        const url = new URL(window.location.href);
        if (value) {
            url.searchParams.set(key, value);
        } else {
            url.searchParams.delete(key);
        }
        window.history.replaceState({}, "", url);
    } catch (error) {
        // ignore URL update failures
    }
}

function products() {
    return dashboardData.products || [];
}

function stores() {
    return dashboardData.store_options || [];
}

function contexts() {
    return dashboardData.context_comparison || [];
}

function contextById(id) {
    const cleanId = String(id ?? "");
    return contexts().find((context) => String(context.id) === cleanId) || contexts()[0] || null;
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

function setText(id, value) {
    const element = byId(id);
    if (element) element.textContent = value;
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

function doughnutOptions(formatter = moneyTooltip) {
    return {
        cutout: "58%",
        resizeDelay: 120,
        plugins: {
            legend: {
                position: "bottom",
                labels: { usePointStyle: true, boxWidth: 8, boxHeight: 8 },
            },
            tooltip: {
                backgroundColor: palette.slate,
                callbacks: { label: formatter },
            },
        },
    };
}

function pieOptions(formatter = moneyTooltip) {
    return {
        resizeDelay: 120,
        plugins: {
            legend: {
                position: "bottom",
                labels: { usePointStyle: true, boxWidth: 8, boxHeight: 8 },
            },
            tooltip: {
                backgroundColor: palette.slate,
                callbacks: { label: formatter },
            },
        },
    };
}

function setStatusClass(element, state) {
    if (!element) return;
    element.classList.remove("status-green", "status-yellow", "status-red");
    element.classList.add(`status-${state}`);
}

function updateChart(chart, labels, datasets) {
    if (!chart) return;
    chart.data.labels = labels;
    chart.data.datasets = datasets;
    chart.update();
}

function updateKpis(context) {
    const health = context.health || {};
    setText("incomeKpiValue", formatMoney(context.income));
    setText("fixedKpiValue", formatMoney(context.fixed_expenses));
    setText("variableKpiValue", formatMoney(context.variable_expenses));
    setText("remainingKpiValue", formatMoney(context.remaining));
    setText("incomeKpiNote", context.name || "Contexto seleccionado");
    setText("fixedKpiNote", `Incluye canasta: ${formatMoney(context.basket_monthly)}`);
    setText("remainingKpiNote", health.state === "red" ? "Requiere ajuste inmediato" : "Disponible después de gastos");

    const remainingKpi = byId("remainingKpi");
    if (remainingKpi) {
        remainingKpi.classList.toggle("kpi-danger", Number(context.remaining || 0) < 0);
        remainingKpi.classList.toggle("kpi-warning", health.state === "yellow");
    }
}

function updateHealth(context) {
    const health = context.health || {};
    const panel = byId("financialHealthPanel");
    const score = Math.max(0, Math.min(100, Number(health.score || 0)));

    setStatusClass(panel, health.state || "green");
    setText("healthStatusLabel", health.label || "Saludable");
    setText("healthScore", formatPercent(score));
    setText("healthStatusText", health.message || "");
    setText("basketMonthlyValue", formatMoney(context.basket_monthly));
    setText("basketPerPersonValue", formatMoney(context.basket_monthly_per_person));
    setText("contextEarnersValue", String(context.earners || 0));
    setText("contextPressureValue", formatPercent(context.percent_income));

    const meter = byId("healthMeterFill");
    if (meter) {
        meter.style.width = `${score}%`;
    }

    const alert = byId("negativeBalanceAlert");
    if (alert) {
        alert.hidden = Number(context.remaining || 0) >= 0;
    }
}

function updateContextMeta(context) {
    setText("contextHouseholdValue", context.household_type || "Contexto");
    setText("contextPeopleValue", `${context.people || 0} integrantes: ${context.adults || 0} adultos, ${context.children || 0} niños`);
    setText("contextStoreValue", `Mercado: ${context.store || "Sin datos"}`);
}

function updateContextCharts(context) {
    const expenseDistribution = context.expense_distribution || [];
    updateChart(
        contextCharts.expensePie,
        expenseDistribution.map((item) => item.label),
        [{
            data: expenseDistribution.map((item) => Math.max(Number(item.value || 0), 0)),
            backgroundColor: expenseDistribution.map((_, index) => chartColors[index % chartColors.length]),
            borderWidth: 0,
        }]
    );

    updateChart(
        contextCharts.incomeExpense,
        ["Ingreso Total", "Gasto Fijo", "Gasto Variable", "Saldo Restante"],
        [{
            label: "Monto mensual",
            data: [
                context.income,
                context.fixed_expenses,
                context.variable_expenses,
                context.remaining,
            ],
            backgroundColor: [
                "rgba(37, 99, 235, 0.78)",
                "rgba(15, 118, 110, 0.78)",
                "rgba(245, 158, 11, 0.78)",
                Number(context.remaining || 0) < 0 ? "rgba(229, 72, 77, 0.82)" : "rgba(21, 128, 61, 0.78)",
            ],
            borderRadius: 8,
        }]
    );

    const deficit = Math.max(Math.abs(Math.min(Number(context.remaining || 0), 0)), 0);
    const positiveBalance = Math.max(Number(context.remaining || 0), 0);
    const usedIncome = Math.max(Math.min(Number(context.total_expenses || 0), Number(context.income || 0)), 0);
    const balanceLabels = deficit > 0 ? ["Ingreso usado", "Déficit"] : ["Ingreso usado", "Saldo restante"];
    const balanceData = deficit > 0 ? [usedIncome, deficit] : [usedIncome, positiveBalance];
    const balanceColors = deficit > 0 ? [palette.slate, palette.coral] : [palette.slate, palette.green];
    updateChart(
        contextCharts.balance,
        balanceLabels,
        [{
            data: balanceData,
            backgroundColor: balanceColors,
            borderWidth: 0,
        }]
    );

    updateChart(
        contextCharts.householdBreakdown,
        ["Adultos", "Niños"],
        [{
            label: "Costo mensual de canasta",
            data: [context.adult_basket_monthly, context.children_basket_monthly],
            backgroundColor: ["rgba(37, 99, 235, 0.76)", "rgba(219, 39, 119, 0.72)"],
            borderRadius: 8,
        }]
    );

    const storeCosts = context.store_monthly_costs || [];
    const selectedStore = context.store;
    updateChart(
        contextCharts.storeBasket,
        storeCosts.map((item) => item.store),
        [{
            label: "Canasta mensual",
            data: storeCosts.map((item) => item.total),
            backgroundColor: storeCosts.map((item) => item.store === selectedStore ? "rgba(15, 118, 110, 0.86)" : "rgba(100, 116, 139, 0.42)"),
            borderColor: storeCosts.map((item) => item.store === selectedStore ? palette.teal : palette.line),
            borderWidth: 1,
            borderRadius: 8,
        }]
    );
}

function updateContextDashboard(context) {
    if (!context) return;
    updateContextMeta(context);
    updateKpis(context);
    updateHealth(context);
    updateContextCharts(context);
}

function initContextFinanceCharts() {
    contextCharts.expensePie = createChart("expensePieChart", {
        type: "pie",
        data: { labels: [], datasets: [] },
        options: pieOptions(),
    });
    contextCharts.incomeExpense = createChart("incomeExpenseChart", {
        type: "bar",
        data: { labels: [], datasets: [] },
        options: baseBarOptions({ showLegend: false }),
    });
    contextCharts.balance = createChart("balanceChart", {
        type: "doughnut",
        data: { labels: [], datasets: [] },
        options: doughnutOptions(),
    });
    contextCharts.householdBreakdown = createChart("householdBreakdownChart", {
        type: "bar",
        data: { labels: [], datasets: [] },
        options: baseBarOptions({ showLegend: false }),
    });
    contextCharts.storeBasket = createChart("storeBasketChart", {
        type: "bar",
        data: { labels: [], datasets: [] },
        options: baseBarOptions({ showLegend: false }),
    });
}

function bindContextSelector() {
    const contextSelect = byId("contextSelect");
    const contextFromUrl = getSearchParam("context");
    const initialContext = contextById(contextFromUrl || contextSelect?.value);
    if (contextSelect && initialContext) {
        contextSelect.value = String(initialContext.id);
        contextSelect.addEventListener("change", (event) => {
            setSearchParam("context", String(event.target.value || ""));
            updateContextDashboard(contextById(event.target.value));
        });
    }
    updateContextDashboard(initialContext);
}

function bindStoreSelector() {
    const storeSelect = byId("storeSelect");
    if (!storeSelect) return;

    storeSelect.addEventListener("change", (event) => {
        const selectedStore = String(event.target.value || "");
        try {
            const url = new URL(window.location.href);
            if (selectedStore) {
                url.searchParams.set("store", selectedStore);
            } else {
                url.searchParams.delete("store");
            }

            const contextSelect = byId("contextSelect");
            if (contextSelect?.value) {
                url.searchParams.set("context", contextSelect.value);
            }

            window.location.assign(url.toString());
        } catch (error) {
            window.location.reload();
        }
    });
}

function initMonthlyBudgetByContextChart() {
    const chart = dashboardData.charts?.context_monthly_budget || {};
    createChart("monthlyBudgetByContextChart", {
        type: "bar",
        data: {
            labels: chart.labels || [],
            datasets: [
                {
                    label: "Ingreso Total",
                    data: chart.income || [],
                    backgroundColor: "rgba(37, 99, 235, 0.72)",
                    borderRadius: 8,
                },
                {
                    label: "Gasto Fijo",
                    data: chart.fixed || [],
                    backgroundColor: "rgba(15, 118, 110, 0.72)",
                    borderRadius: 8,
                },
                {
                    label: "Gasto Variable",
                    data: chart.variable || [],
                    backgroundColor: "rgba(245, 158, 11, 0.74)",
                    borderRadius: 8,
                },
                {
                    label: "Saldo Restante",
                    data: chart.remaining || [],
                    backgroundColor: (chart.remaining || []).map((value) => Number(value || 0) < 0 ? "rgba(229, 72, 77, 0.78)" : "rgba(21, 128, 61, 0.72)"),
                    borderRadius: 8,
                },
            ],
        },
        options: baseBarOptions({ showLegend: true }),
    });
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
    initContextFinanceCharts();
    bindStoreSelector();
    bindContextSelector();
    initMonthlyBudgetByContextChart();
    initIncomeBasketChart();
    initPressureChart();
    initPerPersonChart();
    initEarnersScatterChart();
    initPriceRangeChart();
    initAllProductsComparisonChart();
    updateVariationList();
});
