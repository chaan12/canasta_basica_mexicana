function setContextHouseholdPreset(value) {
    const adultsInput = document.getElementById("contextAdults");
    const childrenInput = document.getElementById("contextChildren");
    if (!adultsInput || !childrenInput) return;

    const presets = {
        vive_solo: { adults: 1, children: 0 },
        pareja: { adults: 2, children: 0 },
        familia: { adults: 2, children: 2 },
    };
    const preset = presets[value];
    if (!preset) return;

    adultsInput.value = preset.adults;
    childrenInput.value = preset.children;
}

document.addEventListener("DOMContentLoaded", () => {
    const householdModel = document.getElementById("contextHouseholdModel");
    if (!householdModel) return;

    householdModel.addEventListener("change", (event) => {
        setContextHouseholdPreset(event.target.value);
    });
});
