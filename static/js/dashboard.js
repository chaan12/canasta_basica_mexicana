const palette = {
    pink: "#ff6b8a",
    violet: "#9b5de5",
    gold: "#ffb703",
    cyan: "#00c2d1",
    mint: "#4dd4ac",
    peach: "#ff8a65",
    blue: "#5d7df5",
    ink: "#35284d",
    gray: "#7c7195",
    line: "#e6dcff",
};

const colorSet = [
    palette.pink,
    palette.violet,
    palette.gold,
    palette.cyan,
    palette.mint,
    palette.peach,
    palette.blue,
];

const softColorSet = [
    "rgba(255, 107, 138, 0.2)",
    "rgba(155, 93, 229, 0.18)",
    "rgba(255, 183, 3, 0.24)",
    "rgba(0, 194, 209, 0.18)",
    "rgba(77, 212, 172, 0.18)",
    "rgba(255, 138, 101, 0.18)",
    "rgba(93, 125, 245, 0.18)",
];

Chart.defaults.font.family = "Inter, system-ui, sans-serif";
Chart.defaults.color = palette.gray;
Chart.defaults.responsive = true;
Chart.defaults.maintainAspectRatio = false;

function moneyLabel(value) {
    return `$${Number(value || 0).toLocaleString("es-MX", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    })}`;
}

function percentLabel(value) {
    return `${Number(value || 0).toLocaleString("es-MX", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
    })}%`;
}

function createChart(id, config) {
    const element = document.getElementById(id);
    if (!element) return null;
    return new Chart(element, config);
}

function legendOptions(display = true) {
    return {
        display,
        position: "bottom",
        align: "center",
        labels: {
            usePointStyle: true,
            pointStyle: "circle",
            boxWidth: 8,
            boxHeight: 8,
            padding: 18,
        },
    };
}

function parsedValue(context) {
    if (typeof context.parsed === "number") {
        return context.parsed;
    }

    if (context.parsed && typeof context.parsed.y !== "undefined") {
        return context.parsed.y;
    }

    return 0;
}

function barOptions({ formatter = moneyLabel, horizontal = false, showLegend = true } = {}) {
    return {
        indexAxis: horizontal ? "y" : "x",
        responsive: true,
        maintainAspectRatio: false,
        resizeDelay: 180,
        interaction: { mode: "index", intersect: false },
        plugins: {
            legend: legendOptions(showLegend),
            tooltip: {
                backgroundColor: palette.ink,
                titleColor: "#ffffff",
                bodyColor: "#ffffff",
                padding: 12,
                cornerRadius: 8,
                callbacks: {
                    label: (context) => {
                        const prefix = context.dataset.label ? `${context.dataset.label}: ` : "";
                        return `${prefix}${formatter(parsedValue(context))}`;
                    },
                },
            },
        },
        scales: {
            x: {
                beginAtZero: horizontal,
                grid: { display: horizontal, color: palette.line },
                ticks: { maxRotation: 0, autoSkip: true },
            },
            y: {
                beginAtZero: true,
                grid: { color: palette.line },
                ticks: {
                    callback: (value) => formatter(value),
                },
            },
        },
    };
}

function maxValue(values) {
    return Math.max(...values.map((value) => Number(value || 0)), 1);
}

function normalize(value, max) {
    return Math.round((Number(value || 0) / max) * 100);
}

function buildRadarDatasets(charts) {
    const labels = charts.contexts.labels || [];
    const totals = charts.contexts.values || [];
    const perPerson = charts.context_per_person.values || [];
    const incomePressure = charts.income.values || [];
    const income = charts.context_income.values || [];
    const people = charts.context_people.values || [];

    const maxTotal = maxValue(totals);
    const maxPerPerson = maxValue(perPerson);
    const maxPressure = maxValue(incomePressure);
    const maxIncome = maxValue(income);
    const maxPeople = maxValue(people);

    return labels.map((label, index) => ({
        label,
        data: [
            normalize(totals[index], maxTotal),
            normalize(perPerson[index], maxPerPerson),
            normalize(incomePressure[index], maxPressure),
            normalize(income[index], maxIncome),
            normalize(people[index], maxPeople),
        ],
        borderColor: colorSet[index % colorSet.length],
        backgroundColor: softColorSet[index % softColorSet.length],
        pointBackgroundColor: colorSet[index % colorSet.length],
        pointBorderColor: "#ffffff",
        borderWidth: 2,
    }));
}

function initDashboardCharts(data) {
    const charts = data.charts || {};

    createChart("contextTotalsChart", {
        type: "bar",
        data: {
            labels: charts.contexts.labels,
            datasets: [{
                label: "Costo total",
                data: charts.contexts.values,
                backgroundColor: charts.contexts.values.map((_, index) => colorSet[index % colorSet.length]),
                borderColor: charts.contexts.values.map((_, index) => colorSet[index % colorSet.length]),
                borderWidth: 1,
                borderRadius: 8,
            }],
        },
        options: barOptions({ formatter: moneyLabel, showLegend: false }),
    });

    createChart("contextPerPersonChart", {
        type: "bar",
        data: {
            labels: charts.context_per_person.labels,
            datasets: [{
                label: "Costo por persona",
                data: charts.context_per_person.values,
                backgroundColor: charts.context_per_person.values.map((_, index) => softColorSet[index % softColorSet.length]),
                borderColor: charts.context_per_person.values.map((_, index) => colorSet[index % colorSet.length]),
                borderWidth: 2,
                borderRadius: 8,
            }],
        },
        options: barOptions({ formatter: moneyLabel, horizontal: true, showLegend: false }),
    });

    createChart("contextIncomeChart", {
        type: "bar",
        data: {
            labels: charts.income.labels,
            datasets: [{
                label: "Porcentaje del ingreso",
                data: charts.income.values,
                backgroundColor: charts.income.values.map((_, index) => colorSet[index % colorSet.length]),
                borderColor: charts.income.values.map((_, index) => colorSet[index % colorSet.length]),
                borderWidth: 1,
                borderRadius: 8,
            }],
        },
        options: barOptions({ formatter: percentLabel, horizontal: true, showLegend: false }),
    });

    createChart("storesByContextChart", {
        type: "bar",
        data: {
            labels: charts.store_contexts.labels,
            datasets: (charts.store_contexts.datasets || []).map((dataset, index) => ({
                label: dataset.label,
                data: dataset.values,
                backgroundColor: softColorSet[index % softColorSet.length],
                borderColor: colorSet[index % colorSet.length],
                borderWidth: 2,
                borderRadius: 8,
            })),
        },
        options: barOptions({ formatter: moneyLabel, showLegend: true }),
    });

    const scatterPoints = (charts.contexts.labels || []).map((label, index) => ({
        x: Number(charts.context_income.values[index] || 0),
        y: Number(charts.contexts.values[index] || 0),
        label,
    }));

    createChart("scatterChart", {
        type: "scatter",
        data: {
            datasets: [{
                label: "Ingreso contra costo",
                data: scatterPoints,
                backgroundColor: colorSet.map((color) => color),
                borderColor: "#ffffff",
                borderWidth: 2,
                pointRadius: 7,
                pointHoverRadius: 9,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            resizeDelay: 180,
            plugins: {
                legend: legendOptions(true),
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const point = context.raw;
                            return `${point.label}: ingreso ${moneyLabel(point.x)}, costo ${moneyLabel(point.y)}`;
                        },
                        title: () => "",
                    },
                },
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { color: palette.line },
                    title: { display: true, text: "Ingreso mensual" },
                    ticks: { callback: (value) => moneyLabel(value) },
                },
                y: {
                    beginAtZero: true,
                    grid: { color: palette.line },
                    title: { display: true, text: "Costo de canasta" },
                    ticks: { callback: (value) => moneyLabel(value) },
                },
            },
        },
    });

    createChart("radarChart", {
        type: "radar",
        data: {
            labels: ["Costo total", "Costo por persona", "% ingreso", "Ingreso mensual", "Personas"],
            datasets: buildRadarDatasets(charts),
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            resizeDelay: 180,
            plugins: {
                legend: legendOptions(true),
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.dataset.label}: ${context.parsed.r}%`,
                    },
                },
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    angleLines: { color: palette.line },
                    grid: { color: palette.line },
                    pointLabels: { color: palette.ink },
                    ticks: { display: false },
                },
            },
        },
    });
}

document.addEventListener("DOMContentLoaded", () => {
    if (window.dashboardData) {
        initDashboardCharts(window.dashboardData);
    }
});
