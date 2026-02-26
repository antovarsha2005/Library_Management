document.addEventListener("DOMContentLoaded", () => {
    const revealElements = Array.from(document.querySelectorAll(".reveal-up"));
    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry, index) => {
                    if (!entry.isIntersecting) {
                        return;
                    }
                    setTimeout(() => {
                        entry.target.classList.add("visible");
                    }, index * 55);
                    observer.unobserve(entry.target);
                });
            },
            { threshold: 0.14 }
        );
        revealElements.forEach((element) => observer.observe(element));
    } else {
        revealElements.forEach((element, index) => {
            setTimeout(() => element.classList.add("visible"), 80 + index * 55);
        });
    }

    const flashItems = document.querySelectorAll(".flash-item, .alert");
    if (flashItems.length) {
        setTimeout(() => {
            flashItems.forEach((item) => {
                item.style.opacity = "0";
                item.style.transform = "translateY(-6px)";
                item.style.transition = "opacity 0.35s ease, transform 0.35s ease";
                setTimeout(() => item.remove(), 360);
            });
        }, 4600);
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

    const syncFloatingState = (field) => {
        if (!field) {
            return;
        }
        const isSelect = field.tagName === "SELECT";
        const hasValue = isSelect ? field.value !== "" : field.value.trim() !== "";
        field.classList.toggle("has-value", hasValue);
    };

    document.querySelectorAll(".field-wrap input, .field-wrap select").forEach((field) => {
        syncFloatingState(field);
        field.addEventListener("input", () => syncFloatingState(field));
        field.addEventListener("change", () => syncFloatingState(field));
        field.addEventListener("blur", () => syncFloatingState(field));
    });

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
