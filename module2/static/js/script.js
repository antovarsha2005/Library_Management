document.addEventListener("DOMContentLoaded", () => {
    const clickableCards = document.querySelectorAll(".clickable-card");

    clickableCards.forEach((card) => {
        card.addEventListener("click", (event) => {
            if (event.target.closest("a, button")) {
                return;
            }
            const href = card.getAttribute("data-href");
            if (href) {
                window.location.href = href;
            }
        });
    });

    const flashes = document.querySelectorAll(".flash");
    if (flashes.length > 0) {
        setTimeout(() => {
            flashes.forEach((item) => {
                item.style.opacity = "0";
                item.style.transition = "opacity 0.35s ease";
                setTimeout(() => item.remove(), 350);
            });
        }, 3200);
    }

    const deleteForms = document.querySelectorAll(".js-confirm-delete");
    deleteForms.forEach((form) => {
        form.addEventListener("submit", (event) => {
            const message = form.getAttribute("data-confirm") || "Are you sure you want to delete this user?";
            if (!window.confirm(message)) {
                event.preventDefault();
            }
        });
    });
});
