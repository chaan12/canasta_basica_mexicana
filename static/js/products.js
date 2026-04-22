function createPriceRow() {
    const row = document.createElement("div");
    row.className = "price-row";
    row.innerHTML = `
        <label>
            Tienda
            <input type="text" name="store_name[]" placeholder="Ej. Walmart" required>
        </label>
        <label>
            Precio
            <input type="number" name="price[]" min="0.01" step="0.01" placeholder="0.00" required>
        </label>
        <button class="button ghost remove-price" type="button">Quitar</button>
    `;
    return row;
}

function refreshRemoveButtons(container) {
    const rows = container.querySelectorAll(".price-row");
    rows.forEach((row) => {
        const button = row.querySelector(".remove-price");
        button.disabled = rows.length === 1;
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("priceRows");
    const addButton = document.getElementById("addPriceButton");
    if (!container || !addButton) return;

    addButton.addEventListener("click", () => {
        container.appendChild(createPriceRow());
        refreshRemoveButtons(container);
    });

    container.addEventListener("click", (event) => {
        const button = event.target.closest(".remove-price");
        if (!button) return;
        const rows = container.querySelectorAll(".price-row");
        if (rows.length <= 1) return;
        button.closest(".price-row").remove();
        refreshRemoveButtons(container);
    });

    refreshRemoveButtons(container);
});
