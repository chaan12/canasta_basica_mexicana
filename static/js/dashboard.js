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

function readDashboardData() {
    const element = document.getElementById("dashboard-data");
    if (!element) return window.dashboardData || {};

    try {
        return JSON.parse(element.textContent || "{}");
    } catch (error) {
        return {};
    }
}

const dashboardData = readDashboardData();
const contextCharts = {};
const allCharts = [];

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

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll("\"", "&quot;")
        .replaceAll("'", "&#039;");
}

function alphabeticalCompare(left, right) {
    return String(left ?? "").localeCompare(String(right ?? ""), "es-MX", {
        sensitivity: "base",
        numeric: true,
    });
}

function formatSignedMoney(value) {
    const amount = Number(value || 0);
    return `${amount > 0 ? "+" : ""}${formatMoney(amount)}`;
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
    const chart = new Chart(element, config);
    allCharts.push(chart);
    return chart;
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

function storeFinanceRows(context) {
    const monthlyIncome = Number(context.income || 0);
    const basketMonthly = Number(context.basket_monthly || 0);
    const fixedBase = Number(context.fixed_expenses || 0) - basketMonthly;
    const variable = Number(context.variable_expenses || 0);
    const storeCosts = context.store_monthly_costs?.length
        ? context.store_monthly_costs
        : [{ store: context.store || "Sin datos", total: basketMonthly }];

    return storeCosts.map((item) => {
        const fixed = fixedBase + Number(item.total || 0);
        const remaining = monthlyIncome - fixed - variable;
        return {
            store: item.store,
            basket: Number(item.total || 0),
            fixed,
            variable,
            remaining,
        };
    });
}

function renderStoreValueList(id, rows, key) {
    const container = byId(id);
    if (!container) return;

    container.innerHTML = rows.map((row) => `
        <div class="store-value-row${key === "remaining" && row[key] < 0 ? " negative" : ""}">
            <span>${escapeHtml(row.store)}</span>
            <b>${formatMoney(row[key])}</b>
        </div>
    `).join("");
}

function storeRiskState(row, monthlyIncome) {
    const ratio = monthlyIncome ? Number(row.remaining || 0) / monthlyIncome : 0;
    if (Number(row.remaining || 0) < 0 || ratio < 0.05) {
        return {
            state: "red",
            label: "Riesgo alto",
            detail: "Saldo crítico",
        };
    }
    if (ratio < 0.15) {
        return {
            state: "yellow",
            label: "Alerta",
            detail: "Margen limitado",
        };
    }
    return {
        state: "green",
        label: "Estable",
        detail: "Margen sano",
    };
}

function renderStoreRiskList(context) {
    const container = byId("storeRiskList");
    if (!container || !context) return;

    const monthlyIncome = Number(context.income || 0);
    const rows = storeFinanceRows(context);

    container.innerHTML = rows.map((row) => {
        const risk = storeRiskState(row, monthlyIncome);
        return `
            <article class="store-risk-item risk-${risk.state}">
                <span class="risk-light" aria-hidden="true"></span>
                <div>
                    <strong>${escapeHtml(row.store)}</strong>
                    <small>${risk.label} · ${risk.detail}</small>
                </div>
                <b>${formatMoney(row.remaining)}</b>
            </article>
        `;
    }).join("");
}

function updateKpis(context) {
    const health = context.health || {};
    const rows = storeFinanceRows(context);
    const fixedValues = rows.map((row) => row.fixed);
    const remainingValues = rows.map((row) => row.remaining);

    setText("incomeKpiValue", formatMoney(context.income));
    setText("fixedKpiValue", `Desde ${formatMoney(Math.min(...fixedValues, Number(context.fixed_expenses || 0)))}`);
    setText("variableKpiValue", formatMoney(context.variable_expenses));
    setText("remainingKpiValue", `Mejor ${formatMoney(Math.max(...remainingValues, Number(context.remaining || 0)))}`);
    setText("incomeKpiNote", context.name || "Contexto seleccionado");
    renderStoreValueList("fixedStoreValues", rows, "fixed");
    renderStoreValueList("variableStoreValues", rows, "variable");
    renderStoreValueList("remainingStoreValues", rows, "remaining");

    const remainingKpi = byId("remainingKpi");
    if (remainingKpi) {
        remainingKpi.classList.toggle("kpi-danger", remainingValues.some((value) => value < 0));
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
    setText("contextStoreValue", `Mejor tienda: ${context.store || "Sin datos"}`);
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
    renderStoreRiskList(context);
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

function initPriceGapChart() {
    const sortedProducts = [...products()]
        .sort((left, right) => Number(right.price_variance || 0) - Number(left.price_variance || 0));

    createChart("priceGapChart", {
        type: "bar",
        data: {
            labels: sortedProducts.map((product) => product.name),
            datasets: [{
                label: "Ahorro potencial",
                data: sortedProducts.map((product) => Number(product.price_variance || 0)),
                backgroundColor: sortedProducts.map((product) => {
                    const variance = Number(product.price_variance || 0);
                    if (variance >= 20) return "rgba(229, 72, 77, 0.78)";
                    if (variance >= 10) return "rgba(245, 158, 11, 0.76)";
                    return "rgba(15, 118, 110, 0.72)";
                }),
                borderRadius: 8,
            }],
        },
        options: baseBarOptions({ horizontal: true, showLegend: false }),
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

function productStorePrice(product, store) {
    return Number(product.prices?.[store] || 0);
}

function renderProductStoreTable() {
    const tableBody = byId("productStoreTableBody");
    const filter = byId("productStoreFilter");
    if (!tableBody) return;

    const selectedStore = String(filter?.value || "");
    const rows = products()
        .map((product) => {
            const selectedPrice = selectedStore ? productStorePrice(product, selectedStore) : Number(product.cheapest_price || 0);
            const cheapest = Number(product.cheapest_price || cheapestPrice(product));
            return {
                product,
                selectedPrice,
                cheapest,
                difference: selectedStore ? selectedPrice - cheapest : 0,
            };
        })
        .filter((row) => !selectedStore || row.selectedPrice > 0)
        .sort((left, right) => alphabeticalCompare(left.product.name, right.product.name));

    tableBody.innerHTML = rows.map(({ product, selectedPrice, cheapest, difference }) => `
        <tr>
            <td>${escapeHtml(product.name)}</td>
            <td>${escapeHtml(product.presentation)}</td>
            <td>${selectedStore ? `${escapeHtml(selectedStore)}: ${formatMoney(selectedPrice)}` : formatMoney(cheapest)}</td>
            <td>${escapeHtml(product.cheapest_store || "Sin datos")}: ${formatMoney(cheapest)}</td>
            <td class="${difference > 0 ? "price-difference" : ""}">${selectedStore ? formatSignedMoney(difference) : "-"}</td>
            <td>${formatMoney(product.average_market_price)}</td>
            <td>${formatMoney(product.price_variance)}</td>
        </tr>
    `).join("");
}

function sortSelectOptionsAlphabetically(selectId) {
    const select = byId(selectId);
    if (!select) return;

    const defaultOption = select.querySelector('option[value=""]');
    const sortedOptions = [...select.querySelectorAll('option:not([value=""])')]
        .sort((left, right) => alphabeticalCompare(left.textContent, right.textContent));

    select.innerHTML = "";
    if (defaultOption) {
        select.appendChild(defaultOption);
    }
    sortedOptions.forEach((option) => select.appendChild(option));
}

function bindProductStoreFilter() {
    const filter = byId("productStoreFilter");
    if (!filter) return;

    sortSelectOptionsAlphabetically("productStoreFilter");
    filter.addEventListener("change", renderProductStoreTable);
    renderProductStoreTable();
}

function heatmapClass(product, price) {
    if (!price) return "missing";
    const low = cheapestPrice(product);
    const high = highestPrice(product);
    if (price === low) return "best";
    if (high <= low) return "low";

    const ratio = (price - low) / (high - low);
    if (ratio <= 0.34) return "low";
    if (ratio <= 0.67) return "mid";
    return "high";
}

function renderPriceHeatmap() {
    const table = byId("priceHeatmapTable");
    if (!table) return;

    const headerCells = stores().map((store) => `<th>${escapeHtml(store)}</th>`).join("");
    const bodyRows = products().map((product) => {
        const priceCells = stores().map((store) => {
            const price = productStorePrice(product, store);
            const className = heatmapClass(product, price);
            const difference = price ? price - Number(product.cheapest_price || cheapestPrice(product)) : 0;
            return `
                <td class="heatmap-price ${className}" data-store="${escapeHtml(store)}">
                    <strong>${price ? formatMoney(price) : "-"}</strong>
                    <small>${price && difference > 0 ? `+${formatMoney(difference)}` : price ? "mejor" : "sin dato"}</small>
                </td>
            `;
        }).join("");

        return `
            <tr>
                <th scope="row">
                    <strong>${escapeHtml(product.name)}</strong>
                    <small>${escapeHtml(product.presentation)}</small>
                </th>
                ${priceCells}
            </tr>
        `;
    }).join("");

    table.innerHTML = `
        <thead>
            <tr>
                <th>Producto</th>
                ${headerCells}
            </tr>
        </thead>
        <tbody>${bodyRows}</tbody>
    `;
}

function activateDashboardTab(targetId) {
    document.querySelectorAll(".dashboard-tab").forEach((tab) => {
        const isActive = tab.dataset.tabTarget === targetId;
        tab.classList.toggle("active", isActive);
        tab.setAttribute("aria-selected", String(isActive));
    });

    document.querySelectorAll(".dashboard-panel").forEach((panel) => {
        const isActive = panel.id === targetId;
        panel.classList.toggle("active", isActive);
        panel.hidden = !isActive;
    });

    window.setTimeout(() => {
        allCharts.forEach((chart) => chart.resize());
    }, 0);
}

function bindDashboardTabs() {
    document.querySelectorAll(".dashboard-tab").forEach((tab) => {
        tab.addEventListener("click", () => activateDashboardTab(tab.dataset.tabTarget));
    });
}

document.addEventListener("DOMContentLoaded", () => {
    bindDashboardTabs();
    initContextFinanceCharts();
    bindContextSelector();
    initMonthlyBudgetByContextChart();
    initIncomeBasketChart();
    initPressureChart();
    initPerPersonChart();
    initEarnersScatterChart();
    initPriceGapChart();
    initPriceRangeChart();
    initAllProductsComparisonChart();
    updateVariationList();
    bindProductStoreFilter();
    renderPriceHeatmap();
});
