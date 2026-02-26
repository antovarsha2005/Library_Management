document.addEventListener("DOMContentLoaded", () => {
    const revealElements = document.querySelectorAll(".reveal-up");
    revealElements.forEach((element, index) => {
        setTimeout(() => {
            element.classList.add("visible");
        }, 90 + index * 70);
    });

    const alerts = document.querySelectorAll(".alert");
    if (alerts.length) {
        setTimeout(() => {
            alerts.forEach((alert) => {
                alert.style.opacity = "0";
                alert.style.transform = "translateY(-6px)";
                alert.style.transition = "opacity 0.35s ease, transform 0.35s ease";
                setTimeout(() => {
                    alert.remove();
                }, 360);
            });
        }, 4200);
    }

    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener("click", (event) => {
            const targetId = anchor.getAttribute("href");
            if (!targetId || targetId.length < 2) {
                return;
            }

            const target = document.querySelector(targetId);
            if (!target) {
                return;
            }

            event.preventDefault();
            target.scrollIntoView({ behavior: "smooth", block: "start" });
        });
    });

    const nameInput = document.querySelector('input[name="name"]');
    const avatar = document.querySelector(".avatar");
    if (nameInput && avatar) {
        const syncAvatar = () => {
            const firstChar = nameInput.value.trim().charAt(0).toUpperCase();
            avatar.textContent = firstChar || "U";
        };
        syncAvatar();
        nameInput.addEventListener("input", syncAvatar);
    }

    document.querySelectorAll(".toggle-pass").forEach((button) => {
        button.addEventListener("click", () => {
            const targetId = button.getAttribute("data-target");
            const targetInput = targetId ? document.getElementById(targetId) : null;
            if (!targetInput) {
                return;
            }

            const showing = targetInput.type === "text";
            targetInput.type = showing ? "password" : "text";
            button.textContent = showing ? "Show" : "Hide";
            button.classList.toggle("is-visible", !showing);
        });
    });

    const signupForm = document.querySelector('form[action$="/signup"]');
    if (signupForm) {
        const passwordInput = signupForm.querySelector('input[name="password"]');
        const confirmPasswordInput = signupForm.querySelector('input[name="confirm_password"]');
        if (passwordInput && confirmPasswordInput) {
            const syncConfirmValidation = () => {
                if (
                    confirmPasswordInput.value &&
                    passwordInput.value !== confirmPasswordInput.value
                ) {
                    confirmPasswordInput.setCustomValidity("Passwords do not match.");
                    return;
                }
                confirmPasswordInput.setCustomValidity("");
            };

            passwordInput.addEventListener("input", syncConfirmValidation);
            confirmPasswordInput.addEventListener("input", syncConfirmValidation);
            signupForm.addEventListener("submit", syncConfirmValidation);
        }
    }
});
