document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm || "Are you sure?")) event.preventDefault();
    });
  });
  // Any select option named "Other" reveals its companion free-text input.
  document.querySelectorAll("select[data-other-select]").forEach((select) => {
    const label = select.closest("label");
    const otherInput = label ? label.querySelector("[data-other-input]") : null;
    if (!otherInput) return;
    const update = () => {
      const show = select.value === "Other";
      otherInput.hidden = !show;
      otherInput.required = show;
      if (!show) otherInput.setCustomValidity("");
    };
    select.addEventListener("change", update);
    update();
  });
  document.querySelectorAll(".flash").forEach((flash) => {
    window.setTimeout(() => {
      flash.classList.add("flash-hide");
      window.setTimeout(() => flash.remove(), 350);
    }, 4500);
  });
});
