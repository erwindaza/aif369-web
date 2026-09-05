const AIF369_PRODUCTS = {
    "engineering-with-ai-masterclass": {
        name: "Engineering with AI Masterclass",
        priceLabel: "CLP $24.990",
        currency: "CLP",
        next: "dashboard/courses.html"
    },
    "private-ai-class": {
        name: "Private AI / Data / Cloud Class",
        priceLabel: "CLP $39.990",
        currency: "CLP",
        next: "dashboard/bookings.html"
    },
    "engineering-with-ai-full-program": {
        name: "Engineering with AI Full Program",
        priceLabel: "CLP $299.990",
        currency: "CLP",
        next: "dashboard/courses.html"
    },
    "corporate-engineering-ai-workshop": {
        name: "Engineering with AI - Corporate",
        priceLabel: "Desde CLP $300.000",
        currency: "CLP",
        next: "corporate-training.html#lead"
    },
    "ai-opportunity-assessment": {
        name: "AI Opportunity Assessment",
        priceLabel: "Desde USD $5,000",
        currency: "USD",
        next: "ai-opportunity-assessment.html#lead"
    }
};

function revenueBackendUrl() {
    const host = window.location.hostname;
    if (host === "aif369.com" || host === "www.aif369.com") {
        return "https://aif369-backend-api-830685315001.us-central1.run.app";
    }
    return "https://aif369-backend-api-dev-830685315001.us-central1.run.app";
}

function moneyProductFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get("product") || "engineering-with-ai-masterclass";
}

function initRevenuePage() {
    const productId = moneyProductFromUrl();
    const product = AIF369_PRODUCTS[productId] || AIF369_PRODUCTS["engineering-with-ai-masterclass"];
    document.querySelectorAll("[data-product-name]").forEach((el) => { el.textContent = product.name; });
    document.querySelectorAll("[data-product-price]").forEach((el) => { el.textContent = product.priceLabel; });
    document.querySelectorAll("[data-checkout-link]").forEach((el) => {
        el.setAttribute("href", "checkout.html?product=" + encodeURIComponent(productId));
    });
    document.querySelectorAll("[data-checkout-product]").forEach((el) => {
        el.value = productId;
    });
}

async function initRevenueCheckout() {
    const form = document.getElementById("revenue-checkout-form");
    const paypalContainer = document.getElementById("revenue-paypal-buttons");
    if (!form || !paypalContainer) return;

    const backendUrl = revenueBackendUrl();
    const productId = moneyProductFromUrl();
    const product = AIF369_PRODUCTS[productId] || AIF369_PRODUCTS["engineering-with-ai-masterclass"];
    initRevenuePage();

    const storedName = localStorage.getItem("aif369_student_name") || "";
    const storedEmail = localStorage.getItem("aif369_student_email") || "";
    const nameField = document.getElementById("checkout-name");
    const emailField = document.getElementById("checkout-email");
    if (nameField && storedName) nameField.value = storedName;
    if (emailField && storedEmail) emailField.value = storedEmail;

    let clientId = "";
    try {
        const configResponse = await fetch(backendUrl + "/api/config/paypal");
        const config = await configResponse.json();
        clientId = config.client_id || "";
    } catch (error) {
        paypalContainer.innerHTML = "<p class=\"revenue-alert revenue-alert-error\">Pagos no disponibles. Escríbenos por WhatsApp para activar tu compra.</p>";
        return;
    }

    if (!clientId) {
        paypalContainer.innerHTML = "<p class=\"revenue-alert revenue-alert-error\">PayPal no está configurado todavía.</p>";
        return;
    }

    const script = document.createElement("script");
    script.src = "https://www.paypal.com/sdk/js?client-id=" + encodeURIComponent(clientId) + "&components=buttons&currency=" + encodeURIComponent(product.currency || "USD");
    script.onload = () => {
        paypal.Buttons({
            style: { layout: "vertical", color: "gold", shape: "rect", label: "pay", height: 45 },
            createOrder: async () => {
                if (!form.reportValidity()) return;
                const email = document.getElementById("checkout-email").value.trim().toLowerCase();
                const response = await fetch(backendUrl + "/api/paypal/revenue/create-order", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, product_id: productId })
                });
                const data = await response.json();
                if (!response.ok || !data.orderID) throw new Error(data.error || "No se pudo crear la orden");
                return data.orderID;
            },
            onApprove: async (data) => {
                const email = document.getElementById("checkout-email").value.trim().toLowerCase();
                const response = await fetch(backendUrl + "/api/paypal/revenue/capture-order", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ orderID: data.orderID, email, product_id: productId })
                });
                const result = await response.json();
                if (!response.ok || result.status !== "COMPLETED" || result.access_status !== "ACTIVE" || !result.access_token) {
                    throw new Error(result.error || "Pago no completado");
                }
                localStorage.setItem("aif369_student_email", email);
                localStorage.setItem("aif369_last_order", data.orderID);
                localStorage.setItem("aif369_access_token:" + productId, result.access_token);
                window.location.href = "payment/success.html?orderID=" + encodeURIComponent(data.orderID) + "&product=" + encodeURIComponent(productId);
            },
            onCancel: () => {
                window.location.href = "payment/cancelled.html?product=" + encodeURIComponent(productId);
            },
            onError: (error) => {
                console.error(error);
                paypalContainer.insertAdjacentHTML("beforebegin", "<p class=\"revenue-alert revenue-alert-error\">No pudimos procesar el pago. Intenta nuevamente o contáctanos.</p>");
            }
        }).render("#revenue-paypal-buttons");
    };
    script.onerror = () => {
        paypalContainer.innerHTML = "<p class=\"revenue-alert revenue-alert-error\">No se pudo cargar PayPal.</p>";
    };
    document.head.appendChild(script);
}

async function initAccessCheck() {
    const blocks = document.querySelectorAll("[data-access-product]");
    if (!blocks.length) return;
    blocks.forEach((block) => {
        const productId = block.getAttribute("data-access-product");
        const accessToken = localStorage.getItem("aif369_access_token:" + productId) || "";
        if (!accessToken) {
            block.innerHTML = "<p class=\"revenue-alert\">Completa tu compra en este navegador para ver este contenido.</p>";
            return;
        }
        fetch(revenueBackendUrl() + "/api/revenue/access", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ access_token: accessToken })
        })
        .then((response) => response.json())
        .then((access) => {
            if (access.access_status === "ACTIVE") {
                block.classList.remove("is-locked");
                block.querySelectorAll("[data-paid-content]").forEach((el) => { el.hidden = false; });
                block.querySelectorAll("[data-locked-content]").forEach((el) => { el.hidden = true; });
            }
        })
        .catch(() => {
            block.insertAdjacentHTML("beforeend", "<p class=\"revenue-alert revenue-alert-error\">No se pudo verificar el acceso.</p>");
        });
    });
}

async function initStudentIntake() {
    const form = document.querySelector("[data-student-intake-form]");
    if (!form) return;

    const backendUrl = revenueBackendUrl();
    const productId = form.getAttribute("data-product-id") || moneyProductFromUrl();
    const submitButton = form.querySelector('button[type="submit"]');

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!form.reportValidity()) return;

        const payload = {
            product_id: productId,
            full_name: (form.querySelector('[name="full_name"]')?.value || "").trim(),
            email: (form.querySelector('[name="email"]')?.value || "").trim().toLowerCase(),
            phone: (form.querySelector('[name="phone"]')?.value || "").trim(),
            country: (form.querySelector('[name="country"]')?.value || "").trim(),
            role: (form.querySelector('[name="role"]')?.value || "").trim(),
            company: (form.querySelector('[name="company"]')?.value || "").trim(),
            message: (form.querySelector('[name="message"]')?.value || "").trim(),
            source_page: window.location.pathname
        };

        if (submitButton) submitButton.disabled = true;

        try {
            const response = await fetch(backendUrl + "/api/student-enrollments", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.error || "No se pudo guardar la inscripción");
            }
            localStorage.setItem("aif369_student_name", payload.full_name);
            localStorage.setItem("aif369_student_email", payload.email);
            window.location.href = data.next_url || ("checkout.html?product=" + encodeURIComponent(productId));
        } catch (error) {
            const existing = form.querySelector(".revenue-alert-error");
            if (existing) existing.remove();
            form.insertAdjacentHTML("beforebegin", "<p class=\"revenue-alert revenue-alert-error\">No pudimos guardar tu inscripción. Intenta nuevamente.</p>");
            console.error(error);
        } finally {
            if (submitButton) submitButton.disabled = false;
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initRevenuePage();
    initStudentIntake();
    initRevenueCheckout();
    initAccessCheck();
});
