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

    const floatingFields = Array.from(
        document.querySelectorAll(".field-wrap input, .field-wrap select")
    );

    floatingFields.forEach((field) => {
        syncFloatingState(field);
        field.addEventListener("input", () => syncFloatingState(field));
        field.addEventListener("change", () => syncFloatingState(field));
        field.addEventListener("blur", () => syncFloatingState(field));
    });

    // Handle browser autofill updates that can happen shortly after DOM ready.
    setTimeout(() => {
        floatingFields.forEach((field) => syncFloatingState(field));
    }, 180);

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

    const countUpNodes = Array.from(document.querySelectorAll(".count-up"));
    const animateCount = (node) => {
        if (!node || node.dataset.animated === "true") {
            return;
        }

        const target = Number(node.dataset.target || 0);
        if (!Number.isFinite(target)) {
            return;
        }

        const duration = 1200;
        const startTime = performance.now();
        node.dataset.animated = "true";

        const step = (timestamp) => {
            const elapsed = timestamp - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const currentValue = Math.round(target * eased);
            node.textContent = currentValue.toLocaleString();

            if (progress < 1) {
                requestAnimationFrame(step);
            } else {
                node.textContent = target.toLocaleString();
            }
        };

        requestAnimationFrame(step);
    };

    if (countUpNodes.length) {
        if ("IntersectionObserver" in window) {
            const counterObserver = new IntersectionObserver(
                (entries, observer) => {
                    entries.forEach((entry) => {
                        if (!entry.isIntersecting) {
                            return;
                        }
                        animateCount(entry.target);
                        observer.unobserve(entry.target);
                    });
                },
                { threshold: 0.24 }
            );
            countUpNodes.forEach((node) => counterObserver.observe(node));
        } else {
            countUpNodes.forEach((node) => animateCount(node));
        }
    }

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

    const bindBookCopyValidation = (form) => {
        const totalInput = form.querySelector('input[name="totalCopies"]');
        const availableInput = form.querySelector('input[name="availableCopies"]');
        if (!totalInput || !availableInput) {
            return;
        }

        const validateCopies = () => {
            const total = Number.parseInt(totalInput.value, 10);
            const available = Number.parseInt(availableInput.value, 10);
            const hasBothValues = totalInput.value !== "" && availableInput.value !== "";

            if (hasBothValues && Number.isFinite(total) && Number.isFinite(available) && available > total) {
                availableInput.setCustomValidity("Available copies cannot exceed total copies.");
            } else {
                availableInput.setCustomValidity("");
            }
        };

        totalInput.addEventListener("input", validateCopies);
        availableInput.addEventListener("input", validateCopies);
        form.addEventListener("submit", validateCopies);
    };

    document.querySelectorAll("form").forEach((form) => bindBookCopyValidation(form));

    document.querySelectorAll(".delete-book-form").forEach((form) => {
        form.addEventListener("submit", (event) => {
            const title = form.getAttribute("data-book-title") || "this book";
            const confirmed = window.confirm(`Delete "${title}" from the catalog?`);
            if (!confirmed) {
                event.preventDefault();
            }
        });
    });

    document.querySelectorAll(".book-catalog-card-clickable").forEach((card) => {
        const navigate = () => {
            const targetHref = card.getAttribute("data-href");
            if (targetHref) {
                window.location.href = targetHref;
            }
        };

        card.addEventListener("click", (event) => {
            const interactiveTarget = event.target.closest(
                'a, button, input, select, textarea, form, [data-no-card-nav="true"]'
            );
            if (interactiveTarget) {
                return;
            }
            navigate();
        });

        card.addEventListener("keydown", (event) => {
            if (event.key !== "Enter" && event.key !== " ") {
                return;
            }
            event.preventDefault();
            navigate();
        });
    });
});
