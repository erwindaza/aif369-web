/**
 * ════════════════════════════════════════════════════════════
 * AIF369 — scripts.js
 * ────────────────────────────────────────────────────────────
 * Lógica principal del sitio web AIF369.
 * 
 * Qué hace este archivo:
 * 1. Menú hamburguesa (☰) — abrir/cerrar en celulares
 * 2. Efecto de scroll en la barra de navegación
 * 3. Animaciones al hacer scroll (elementos aparecen suavemente)
 * 4. Formularios de contacto — envío al backend + feedback visual
 * 5. Scorecard IA — cuestionario interactivo de madurez
 * 6. Internacionalización (i18n) — cambio ES ↔ EN
 * 
 * Backend: Cloud Run en GCP (aif369-backend-api)
 * Datos: Se guardan en BigQuery para analytics y seguimiento
 * ════════════════════════════════════════════════════════════
 */
document.addEventListener("DOMContentLoaded", function () {
    // ── Configuración del backend según el entorno ──
    // En producción (aif369.com) usa el backend real; en desarrollo usa uno de prueba
    const PROD_BACKEND_URL = 'https://aif369-backend-api-830685315001.us-central1.run.app';
    const DEV_BACKEND_URL = 'https://aif369-backend-api-dev-830685315001.us-central1.run.app';
    const isProduction = window.location.hostname === 'aif369.com' || window.location.hostname === 'www.aif369.com';
    const BACKEND_URL = isProduction ? PROD_BACKEND_URL : DEV_BACKEND_URL;

    // ── Menú hamburguesa (☰) ──
    // En pantallas pequeñas, el menú se colapsa. Este código lo abre y cierra.
    const toggle = document.querySelector(".nav-toggle");
    const navLinks = document.querySelector(".nav-links");

    if (toggle && navLinks) {
        // Función para cerrar el menú
        function closeMenu() {
            navLinks.classList.remove("active");
            toggle.classList.remove("active");
            toggle.setAttribute("aria-expanded", "false");
            document.body.style.overflow = "";
        }

        // Función para abrir el menú
        function openMenu() {
            navLinks.classList.add("active");
            toggle.classList.add("active");
            toggle.setAttribute("aria-expanded", "true");
            document.body.style.overflow = "hidden";
        }

        // Toggle con click - funciona en desktop y móvil (iOS + Android)
        toggle.addEventListener("click", function(e) {
            e.stopPropagation();
            if (navLinks.classList.contains("active")) {
                closeMenu();
            } else {
                openMenu();
            }
        });

        // Cerrar menú cuando se toca fuera
        document.addEventListener("click", function(e) {
            if (!navLinks.classList.contains("active")) return;
            if (toggle.contains(e.target) || navLinks.contains(e.target)) return;
            closeMenu();
        });

        // Cerrar menú cuando se hace clic en un link del nav
        // Delay para que el navegador procese la navegación antes de cerrar
        navLinks.querySelectorAll("a").forEach(function(link) {
            link.addEventListener("click", function() {
                setTimeout(closeMenu, 150);
            });
        });

        // Cerrar con tecla Escape
        document.addEventListener("keydown", function(e) {
            if (e.key === "Escape" && navLinks.classList.contains("active")) {
                closeMenu();
                toggle.focus();
            }
        });
    }

    // ── Efecto de scroll en la barra de navegación ──
    // Cuando el usuario baja, la barra se vuelve más sólida (clase "scrolled")
    const header = document.querySelector(".site-header");
    let lastScroll = 0;

    window.addEventListener("scroll", () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 50) {
            header.classList.add("scrolled");
        } else {
            header.classList.remove("scrolled");
        }
        
        lastScroll = currentScroll;
    });

    // ══════════════════════════════════════════════════════
    // TRADUCCIONES (i18n) — Español ↔ Inglés
    // Cada clave ("nav.home", "hero.title", etc.) corresponde
    // a un elemento HTML con atributo data-i18n.
    // Al hacer clic en "EN" o "ES", se cambian todos los textos.
    // ══════════════════════════════════════════════════════
    // Translations loaded from /locales/es.json and /locales/en.json
    const translations = { es: {}, en: {} };
    let translationsLoaded = false;

    // Minimal fallback translations (nav only) in case JSON fetch fails
    const fallbackTranslations = {
        es: { "nav.home": "Inicio", "nav.services": "Servicios", "nav.blog": "Insights", "nav.author": "Sobre nosotros", "lang.switch": "EN", "lang.switchAria": "Cambiar a inglés" },
        en: { "nav.home": "Home", "nav.services": "Services", "nav.blog": "Insights", "nav.author": "About us", "lang.switch": "ES", "lang.switchAria": "Switch to Spanish" }
    };

    async function loadTranslations(lang) {
        if (translations[lang] && Object.keys(translations[lang]).length > 10) {
            return; // Already loaded
        }
        try {
            const res = await fetch('/locales/' + lang + '.json');
            if (res.ok) {
                translations[lang] = await res.json();
            } else {
                translations[lang] = fallbackTranslations[lang] || {};
            }
        } catch (e) {
            translations[lang] = fallbackTranslations[lang] || {};
        }
    }

    // Pre-load both languages
    Promise.all([loadTranslations('es'), loadTranslations('en')]).then(function() {
        translationsLoaded = true;
        applyTranslations(getCurrentLanguage());
    });

    const langToggles = document.querySelectorAll(".lang-toggle");

    function updateLangToggles(lang) {
        const dictionary = translations[lang];
        if (!dictionary) {
            return;
        }

        langToggles.forEach((toggle) => {
            if (dictionary["lang.switch"]) {
                toggle.textContent = dictionary["lang.switch"];
            }
            if (dictionary["lang.switchAria"]) {
                toggle.setAttribute("aria-label", dictionary["lang.switchAria"]);
            }
        });
    }

    function applyTranslations(lang) {
        const dictionary = translations[lang];
        if (!dictionary) {
            return;
        }

        document.documentElement.lang = lang;

        document.querySelectorAll("[data-i18n]").forEach((element) => {
            const key = element.dataset.i18n;
            if (dictionary[key]) {
                const val = dictionary[key];
                // Use innerHTML only if translation contains allowed HTML tags
                if (/<(strong|em|a |br|span)\b/.test(val)) {
                    element.innerHTML = val;
                } else {
                    element.textContent = val;
                }
            }
        });

        document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
            const key = element.dataset.i18nPlaceholder;
            if (dictionary[key]) {
                element.setAttribute("placeholder", dictionary[key]);
            }
        });

        document.querySelectorAll("[data-i18n-aria-label]").forEach((element) => {
            const key = element.dataset.i18nAriaLabel;
            if (dictionary[key]) {
                element.setAttribute("aria-label", dictionary[key]);
            }
        });

        document.querySelectorAll("[data-i18n-title]").forEach((element) => {
            const key = element.dataset.i18nTitle;
            if (dictionary[key]) {
                if (element.tagName === "TITLE") {
                    document.title = dictionary[key];
                } else {
                    element.textContent = dictionary[key];
                }
            }
        });

        document.querySelectorAll("[data-i18n-content]").forEach((element) => {
            const key = element.dataset.i18nContent;
            if (dictionary[key]) {
                element.setAttribute("content", dictionary[key]);
            }
        });

        updateLangToggles(lang);
    }

    let activeLanguage = null;

    function readStoredLanguage() {
        try {
            return localStorage.getItem("site-lang");
        } catch (error) {
            return null;
        }
    }

    function persistLanguage(lang) {
        try {
            localStorage.setItem("site-lang", lang);
        } catch (error) {
            activeLanguage = lang;
        }
    }

    function getInitialLanguage() {
        const stored = readStoredLanguage();
        if (stored && translations[stored]) {
            return stored;
        }

        const browserLang = navigator.language || "en";
        if (browserLang.toLowerCase().startsWith("es")) {
            return "es";
        }

        return "en";
    }

    function getCurrentLanguage() {
        const stored = readStoredLanguage();
        return stored || activeLanguage || getInitialLanguage();
    }

    function setLanguage(lang) {
        const target = translations[lang] ? lang : "en";
        activeLanguage = target;
        persistLanguage(target);
        // Ensure translations are loaded before applying
        if (Object.keys(translations[target]).length === 0) {
            loadTranslations(target).then(function() { applyTranslations(target); });
        } else {
            applyTranslations(target);
        }
    }

    if (langToggles.length > 0) {
        langToggles.forEach((langToggle) => {
            langToggle.addEventListener("click", function (event) {
                event.preventDefault();
                event.stopPropagation();
            const current = getCurrentLanguage();
            const next = current === "es" ? "en" : "es";
            setLanguage(next);
            // Track language toggle in GA4
            if (window.aif369 && window.aif369.trackEvent) {
                window.aif369.trackEvent('language_toggle', { from_lang: current, to_lang: next });
            }
            });
        });
    }

    // ══════════════════════════════════════════════════════
    // FORMULARIOS DE CONTACTO
    // Busca todos los formularios con atributo [data-contact-form],
    // los envía al backend (BigQuery + email) y muestra feedback:
    //   click → "Enviando..." → "Enviado ✓" (o error)
    // Máquina de 4 estados: idle / submitting / success / error
    // ══════════════════════════════════════════════════════
    const contactForms = document.querySelectorAll("[data-contact-form]");

    function resolveBackendEndpoint(form, baseUrl = BACKEND_URL) {
        const endpoint = form.dataset.endpoint;
        if (!endpoint) {
            return null;
        }

        if (endpoint.startsWith("http://") || endpoint.startsWith("https://")) {
            return endpoint;
        }

        const normalized = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
        return `${baseUrl}${normalized}`;
    }

    function buildBackendPayload(submission) {
        return {
            name: submission.fullName || submission.name || "",
            email: submission.email || "",
            company: submission.company || "",
            role: submission.role || "",
            interest: submission.interest || "",
            team_size: submission.teamSize || "",
            message: submission.message || submission.context || "Solicitud enviada desde el sitio web.",
            source_page: window.location.href
        };
    }

    contactForms.forEach((form) => {
        const submitBtn = form.querySelector('button[type="submit"], .btn[type="submit"]');
        const statusLine = form.querySelector('.form-status');
        const successMessage = form.querySelector('.form-success');
        const errorMessage = form.querySelector('.form-error');
        let isSubmitting = false;
        let originalButtonText = '';
        let pendingTimer = null;
        let extendedTimer = null;

        // Store original button text and add spinner markup
        if (submitBtn) {
            originalButtonText = submitBtn.textContent.trim();
            submitBtn.innerHTML = '<span class="btn-text">' + originalButtonText + '</span><span class="btn-spinner"></span>';
            submitBtn.style.minWidth = submitBtn.offsetWidth + 'px';
        }

        function setFormState(state, message) {
            if (!submitBtn) return;
            const btnText = submitBtn.querySelector('.btn-text');
            const btnSpinner = submitBtn.querySelector('.btn-spinner');

            // Clear timers
            if (pendingTimer) { clearTimeout(pendingTimer); pendingTimer = null; }
            if (extendedTimer) { clearTimeout(extendedTimer); extendedTimer = null; }

            // Reset all state classes
            form.classList.remove('form-loading', 'form-state-success', 'form-state-error');
            submitBtn.classList.remove('btn-submitting', 'btn-success', 'btn-error');
            submitBtn.removeAttribute('aria-busy');
            if (statusLine) statusLine.hidden = true;
            if (successMessage) successMessage.hidden = true;
            if (errorMessage) errorMessage.hidden = true;

            switch (state) {
                case 'idle':
                    submitBtn.disabled = false;
                    isSubmitting = false;
                    if (btnText) btnText.textContent = originalButtonText;
                    if (btnSpinner) btnSpinner.style.display = 'none';
                    break;

                case 'submitting':
                    submitBtn.disabled = true;
                    isSubmitting = true;
                    submitBtn.classList.add('btn-submitting');
                    submitBtn.setAttribute('aria-busy', 'true');
                    form.classList.add('form-loading');
                    if (btnText) btnText.textContent = 'Enviando...';
                    if (btnSpinner) btnSpinner.style.display = 'inline-block';
                    if (statusLine) {
                        statusLine.textContent = 'Enviando tu solicitud...';
                        statusLine.hidden = false;
                        statusLine.className = 'form-status form-status-pending';
                    }
                    // Progressive feedback: 1.5s extended message
                    extendedTimer = setTimeout(() => {
                        if (statusLine && isSubmitting) {
                            statusLine.textContent = 'Seguimos procesando. No es necesario volver a hacer clic.';
                        }
                    }, 1500);
                    break;

                case 'success':
                    submitBtn.disabled = true;
                    isSubmitting = false;
                    submitBtn.classList.add('btn-success');
                    form.classList.add('form-state-success');
                    if (btnText) btnText.textContent = 'Enviado ✓';
                    if (btnSpinner) btnSpinner.style.display = 'none';
                    if (successMessage) successMessage.hidden = false;
                    if (statusLine) statusLine.hidden = true;
                    // Re-enable form after 5 seconds
                    setTimeout(() => {
                        setFormState('idle');
                        form.reset();
                    }, 5000);
                    break;

                case 'error':
                    submitBtn.disabled = false;
                    isSubmitting = false;
                    submitBtn.classList.add('btn-error');
                    form.classList.add('form-state-error');
                    if (btnText) btnText.textContent = 'Reintentar';
                    if (btnSpinner) btnSpinner.style.display = 'none';
                    if (errorMessage) {
                        errorMessage.textContent = message || 'No pudimos enviar tu solicitud en este momento. Inténtalo nuevamente.';
                        errorMessage.hidden = false;
                    }
                    if (statusLine) statusLine.hidden = true;
                    break;
            }
        }

        form.addEventListener("submit", async function (event) {
            event.preventDefault();

            // Anti double-click: ignore if already submitting
            if (isSubmitting) return;

            // Instant feedback (< 100ms)
            setFormState('submitting');

            const formData = new FormData(form);
            const rawName = formData.get("fullName")?.toString().trim()
                || formData.get("name")?.toString().trim()
                || "";
            const submission = {
                fullName: rawName,
                name: rawName,
                email: formData.get("email")?.toString().trim() || "",
                role: formData.get("role")?.toString().trim() || "",
                company: formData.get("company")?.toString().trim() || "",
                interest: formData.get("interest")?.toString().trim() || "",
                teamSize: formData.get("teamSize")?.toString().trim() || "",
                context: formData.get("context")?.toString().trim() || "",
                message: formData.get("message")?.toString().trim() || "",
                submittedAt: new Date().toISOString()
            };

            // Send to backend with timeout
            const endpoint = resolveBackendEndpoint(form);
            const backendPayload = buildBackendPayload(submission);

            let backendOk = false;
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 10000);

                const response = await fetch(endpoint, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(backendPayload),
                    signal: controller.signal
                });
                clearTimeout(timeoutId);
                backendOk = response.ok;
            } catch (err) {
                backendOk = false;
            }

            if (backendOk) {
                setFormState('success');
                // Track form submission in GA4
                if (window.aif369 && window.aif369.trackEvent) {
                    window.aif369.trackEvent('form_submit', {
                        form_type: form.dataset.contactForm || 'contact',
                        source_page: window.location.pathname
                    });
                }
            } else {
                setFormState('error');
            }
        });
    });

    setLanguage(getInitialLanguage());

    // ══════════════════════════════════════════════════════
    // GOOGLE ANALYTICS 4 — Event Tracking
    // Loads GA4 dynamically and tracks custom events:
    //   page_view, form_submit, scorecard_complete,
    //   chat_start, cta_click, language_toggle,
    //   calendly_open, assessment_interest
    // ══════════════════════════════════════════════════════
    const GA_MEASUREMENT_ID = window.__AIF369_CONFIG__?.GA_MEASUREMENT_ID || '';

    if (GA_MEASUREMENT_ID && GA_MEASUREMENT_ID !== 'G-PLACEHOLDER') {
        // Load gtag.js script
        const gtagScript = document.createElement('script');
        gtagScript.async = true;
        gtagScript.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_MEASUREMENT_ID;
        document.head.appendChild(gtagScript);

        window.dataLayer = window.dataLayer || [];
        function gtag(){ window.dataLayer.push(arguments); }
        window.gtag = gtag;
        gtag('js', new Date());
        gtag('config', GA_MEASUREMENT_ID, {
            page_title: document.title,
            page_location: window.location.href,
            language: getCurrentLanguage()
        });

        // Track CTA clicks (all buttons and .btn links)
        document.addEventListener('click', function(e) {
            var btn = e.target.closest('.btn, button[type="submit"]');
            if (!btn) return;
            var label = btn.textContent.trim().substring(0, 80);
            var href = btn.getAttribute('href') || btn.closest('a')?.getAttribute('href') || '';
            gtag('event', 'cta_click', {
                button_text: label,
                destination_url: href,
                source_page: window.location.pathname
            });

            // Track Calendly opens specifically
            if (label.toLowerCase().includes('agendar') || label.toLowerCase().includes('schedule') ||
                href.includes('calendly')) {
                gtag('event', 'calendly_open', { source_page: window.location.pathname });
            }

            // Track assessment interest
            if (label.toLowerCase().includes('assessment') || label.toLowerCase().includes('starter') ||
                label.toLowerCase().includes('governed') || label.toLowerCase().includes('enterprise')) {
                gtag('event', 'assessment_interest', {
                    package_type: label,
                    source_page: window.location.pathname
                });
            }
        });
    }

    // Expose GA helper for other scripts (chat-widget, forms)
    window.aif369 = window.aif369 || {};
    window.aif369.trackEvent = function(eventName, params) {
        if (window.gtag) {
            window.gtag('event', eventName, params || {});
        }
    };
    window.aif369.getCurrentLanguage = getCurrentLanguage;

    // ══════════════════════════════════════════════════════
    // SMART CTA PERSONALIZATION
    // Tracks page visits in localStorage, shows contextual CTAs
    // based on user behavior (returning visitor, pages seen, etc.)
    // ══════════════════════════════════════════════════════
    (function smartCTA() {
        var STORAGE_KEY = 'aif369_visits';
        var data;
        try {
            data = JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
        } catch (e) {
            data = {};
        }
        // Initialize visit tracking
        if (!data.pages) data.pages = {};
        if (!data.firstVisit) data.firstVisit = Date.now();
        data.lastVisit = Date.now();
        data.totalVisits = (data.totalVisits || 0) + 1;

        // Track current page
        var page = window.location.pathname.replace(/^\//, '').replace(/\.html$/, '') || 'index';
        data.pages[page] = (data.pages[page] || 0) + 1;

        try { localStorage.setItem(STORAGE_KEY, JSON.stringify(data)); } catch (e) {}

        // Determine user segment
        var pageCount = Object.keys(data.pages).length;
        var isReturning = data.totalVisits > 1;
        var hasSeenServices = !!data.pages['services'];
        var hasSeenAssessment = !!data.pages['assessment-caio'];
        var hasSeenScorecard = !!data.pages['scorecard'];
        var hasSeenMethodology = !!data.pages['metodologia'];
        var hasSeenCatalog = !!data.pages['catalogo-soluciones-ia'];

        // Smart CTA logic — pick the most relevant CTA per context
        var lang = getCurrentLanguage();
        var cta = null;

        // Don't show smart CTAs on pages the CTA points to
        if (page === 'assessment-caio' || page === 'scorecard' || page === 'services') {
            // No cross-page CTA on destination pages
        } else if (hasSeenAssessment && !hasSeenScorecard) {
            cta = {
                text: lang === 'es' ? '📊 Mide tu madurez en IA — Scorecard gratuito' : '📊 Measure your AI maturity — Free Scorecard',
                href: 'scorecard.html',
                event: 'smart_cta_scorecard'
            };
        } else if (hasSeenScorecard && !hasSeenAssessment) {
            cta = {
                text: lang === 'es' ? '🎯 ¿Listo para un plan? Conoce el Assessment CAIO' : '🎯 Ready for a plan? Explore the CAIO Assessment',
                href: 'assessment-caio.html',
                event: 'smart_cta_assessment'
            };
        } else if (isReturning && pageCount >= 3 && !hasSeenAssessment) {
            cta = {
                text: lang === 'es' ? '🔍 Ya conoces AIF369 — Descubre tu Assessment personalizado' : '🔍 You know AIF369 — Discover your personalized Assessment',
                href: 'assessment-caio.html',
                event: 'smart_cta_assessment_returning'
            };
        } else if (hasSeenServices && !hasSeenCatalog) {
            cta = {
                text: lang === 'es' ? '📋 Explora nuestras 19 soluciones IA → Catálogo' : '📋 Explore our 19 AI solutions → Catalog',
                href: 'catalogo-soluciones-ia.html',
                event: 'smart_cta_catalog'
            };
        }

        if (!cta) return;

        // Render floating smart CTA bar
        var bar = document.createElement('div');
        bar.className = 'smart-cta-bar';
        bar.innerHTML = '<a href="' + cta.href + '" class="smart-cta-link">' + cta.text + '</a>' +
            '<button class="smart-cta-close" aria-label="Close">&times;</button>';
        document.body.appendChild(bar);

        // Show after 3s delay
        setTimeout(function() { bar.classList.add('visible'); }, 3000);

        // Close button
        bar.querySelector('.smart-cta-close').addEventListener('click', function() {
            bar.classList.remove('visible');
            setTimeout(function() { bar.remove(); }, 300);
        });

        // Track impression + click
        window.aif369.trackEvent('smart_cta_impression', { cta_type: cta.event, page: page });
        bar.querySelector('.smart-cta-link').addEventListener('click', function() {
            window.aif369.trackEvent('smart_cta_click', { cta_type: cta.event, page: page });
        });
    })();
});

/* ═══════════════════════════════════════════════════════════
   ENROLLMENT FORM + PAYPAL SMART BUTTONS
   Flow: Fill form → Validate → Show PayPal → Pay $10 → Success
   ═══════════════════════════════════════════════════════════ */
/* ═══ PayPal SDK Loader (client-id from backend, never hardcoded) ═══ */
var _paypalSDKReady = null; // resolved promise once SDK is loaded

function loadPayPalSDK() {
    if (_paypalSDKReady) return _paypalSDKReady;

    var BACKEND_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'https://aif369-backend-api-dev-830685315001.us-central1.run.app'
        : 'https://aif369-backend-api-830685315001.us-central1.run.app';

    _paypalSDKReady = fetch(BACKEND_URL + '/api/config/paypal')
        .then(function (res) { return res.json(); })
        .then(function (data) {
            if (!data.client_id) throw new Error('No PayPal client_id');
            return new Promise(function (resolve, reject) {
                var script = document.createElement('script');
                script.src = 'https://www.paypal.com/sdk/js?client-id=' + encodeURIComponent(data.client_id) + '&components=buttons&disable-funding=venmo&currency=USD';
                script.onload = resolve;
                script.onerror = function () { reject(new Error('PayPal SDK failed to load')); };
                document.head.appendChild(script);
            });
        });

    return _paypalSDKReady;
}

document.addEventListener('DOMContentLoaded', function () {
    var wrappers = document.querySelectorAll('.enrollment-wrapper');
    if (!wrappers.length) return;

    // Pre-fetch PayPal SDK so it's ready when user finishes the form
    loadPayPalSDK().catch(function (err) { console.warn('PayPal pre-load failed, will retry:', err); });

    wrappers.forEach(function (wrapper) {
        var courseName = wrapper.getAttribute('data-course') || 'Curso AIF369';
        var form = wrapper.querySelector('.enrollment-form');
        var paymentDiv = wrapper.querySelector('.enrollment-payment');
        var successDiv = wrapper.querySelector('.enrollment-success');
        var backBtn = wrapper.querySelector('.enrollment-back');
        var steps = wrapper.querySelectorAll('.enrollment-step');
        var paypalContainer = wrapper.querySelector('.paypal-btn-container');
        var enrollmentData = {};
        var paypalRendered = false;

        function setStep(num) {
            steps.forEach(function (s) {
                var sNum = parseInt(s.getAttribute('data-step'));
                s.classList.remove('active', 'completed');
                if (sNum < num) s.classList.add('completed');
                if (sNum === num) s.classList.add('active');
            });
        }

        // Step 1 → Step 2: Form submit
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            // Clear previous invalid states
            form.querySelectorAll('.invalid').forEach(function (el) { el.classList.remove('invalid'); });

            var name = form.querySelector('[name="name"]');
            var email = form.querySelector('[name="email"]');
            var phone = form.querySelector('[name="phone"]');
            var country = form.querySelector('[name="country"]');
            var valid = true;

            if (!name.value.trim()) { name.classList.add('invalid'); valid = false; }
            if (!email.value.trim() || !email.validity.valid) { email.classList.add('invalid'); valid = false; }
            if (!phone.value.trim()) { phone.classList.add('invalid'); valid = false; }
            if (!country.value) { country.classList.add('invalid'); valid = false; }

            if (!valid) return;

            enrollmentData = {
                name: name.value.trim(),
                email: email.value.trim(),
                phone: phone.value.trim(),
                country: country.value,
                course: courseName,
                source_page: window.location.pathname
            };

            // Show payment step
            wrapper.querySelector('.summary-name').textContent = enrollmentData.name;
            wrapper.querySelector('.summary-email').textContent = enrollmentData.email;
            form.style.display = 'none';
            paymentDiv.style.display = 'block';
            setStep(2);

            // Render PayPal buttons (only once, after SDK loaded)
            if (!paypalRendered) {
                paypalRendered = true;
                loadPayPalSDK().then(function () {
                    if (typeof paypal === 'undefined' || !paypal.Buttons) return;
                    paypal.Buttons({
                    style: {
                        layout: 'vertical',
                        color: 'gold',
                        shape: 'rect',
                        label: 'pay',
                        height: 45
                    },
                    createOrder: function (data, actions) {
                        return actions.order.create({
                            purchase_units: [{
                                description: courseName + ' — AIF369',
                                amount: {
                                    currency_code: 'USD',
                                    value: '10.00'
                                }
                            }]
                        });
                    },
                    onApprove: function (data, actions) {
                        return actions.order.capture().then(function (details) {
                            // Payment successful — send enrollment to backend
                            enrollmentData.paypal_order_id = data.orderID;
                            enrollmentData.payer_email = details.payer && details.payer.email_address ? details.payer.email_address : '';
                            enrollmentData.payment_status = 'completed';

                            sendEnrollment(enrollmentData);

                            // Show success
                            paymentDiv.style.display = 'none';
                            successDiv.style.display = 'block';
                            wrapper.querySelector('.enrollment-steps').style.display = 'none';
                        });
                    },
                    onError: function (err) {
                        console.error('PayPal error:', err);
                        alert('Hubo un error con el pago. Por favor intenta de nuevo o contáctanos por WhatsApp.');
                    }
                }).render(paypalContainer);
                }); // end loadPayPalSDK.then
            }

            // Scroll to payment section
            paymentDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });

        // Back button: payment → form
        if (backBtn) {
            backBtn.addEventListener('click', function () {
                paymentDiv.style.display = 'none';
                form.style.display = 'flex';
                setStep(1);
            });
        }
    });

    // Send enrollment data to backend
    function sendEnrollment(data) {
        var BACKEND_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'https://aif369-backend-api-dev-830685315001.us-central1.run.app'
            : 'https://aif369-backend-api-830685315001.us-central1.run.app';

        fetch(BACKEND_URL + '/api/enrollment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }).catch(function (err) {
            console.warn('Enrollment backend notification failed (payment was successful):', err);
        });
    }
});

/* ═══ Job Board — encuentra-empleo.html ═══ */
(function () {
    var container = document.getElementById('job-listings');
    var searchInput = document.getElementById('job-search');
    if (!container || !searchInput) return;

    var jobs = [
        {
            id: 'BJ-2026-001',
            title: 'Fullstack Cloud Engineer',
            company: 'Empresa confidencial — Sector Tecnología',
            location: 'LATAM (Remoto)',
            modality: 'Remoto | Full-time | Contrato',
            description: 'Desarrollo y mantenimiento de aplicaciones cloud-native. Microservicios, APIs REST/GraphQL, CI/CD pipelines, e integración con servicios cloud (AWS/GCP/Azure). Participación en arquitectura de soluciones escalables.',
            tags: ['React', 'Node.js', 'TypeScript', 'Python', 'AWS', 'GCP', 'Docker', 'Kubernetes', 'Terraform', 'CI/CD', 'PostgreSQL', 'MongoDB', 'GraphQL', 'REST API'],
            requirements: [
                '+4 años de experiencia fullstack',
                'React / Next.js + Node.js / Python',
                'Cloud: AWS o GCP (certificación deseable)',
                'Docker, Kubernetes, IaC (Terraform)',
                'Inglés intermedio-avanzado'
            ],
            excludes: ['Sin experiencia cloud', 'Solo frontend o solo backend sin interés en fullstack'],
            applyUrl: 'https://bejoby.com'
        },
        {
            id: 'BJ-2026-002',
            title: 'Backend Developer',
            company: 'Empresa confidencial — Sector Tecnología',
            location: 'LATAM (Remoto)',
            modality: 'Remoto | Full-time | Contrato',
            description: 'Diseño e implementación de APIs escalables, microservicios y sistemas distribuidos. Integración con bases de datos relacionales y NoSQL, mensajería asíncrona, y pipelines de datos. Colaboración con equipos de producto y DevOps.',
            tags: ['Java', 'Spring Boot', 'Python', 'FastAPI', 'Node.js', 'PostgreSQL', 'Redis', 'Kafka', 'RabbitMQ', 'Docker', 'AWS', 'GCP', 'REST API', 'Microservicios'],
            requirements: [
                '+3 años de experiencia backend',
                'Java (Spring Boot) o Python (FastAPI/Django)',
                'SQL avanzado + NoSQL (Redis, MongoDB)',
                'Mensajería: Kafka o RabbitMQ',
                'Docker, CI/CD, testing automatizado',
                'Inglés intermedio'
            ],
            excludes: ['Sin experiencia en APIs', 'Solo scripts o automatización sin arquitectura'],
            applyUrl: 'https://bejoby.com'
        }
    ];

    function normalize(str) {
        return str.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    }

    function renderJobs(filtered) {
        container.innerHTML = '';
        var noResults = document.getElementById('job-no-results');

        if (filtered.length === 0) {
            if (noResults) noResults.style.display = 'block';
            return;
        }
        if (noResults) noResults.style.display = 'none';

        filtered.forEach(function (job) {
            var card = document.createElement('div');
            card.className = 'job-card';

            var h3 = document.createElement('h3');
            h3.textContent = job.title;
            card.appendChild(h3);

            var meta = document.createElement('p');
            meta.className = 'job-meta';
            meta.textContent = job.company + ' · ' + job.modality + ' · ' + job.location;
            card.appendChild(meta);

            var desc = document.createElement('p');
            desc.className = 'job-desc';
            desc.textContent = job.description;
            card.appendChild(desc);

            var tagsDiv = document.createElement('div');
            tagsDiv.className = 'job-tags';
            job.tags.forEach(function (t) {
                var span = document.createElement('span');
                span.className = 'job-tag';
                span.textContent = t;
                tagsDiv.appendChild(span);
            });
            card.appendChild(tagsDiv);

            var ul = document.createElement('ul');
            ul.style.cssText = 'font-size:0.85rem;color:var(--text-secondary);margin-bottom:var(--space-4);padding-left:20px;line-height:1.8;';
            job.requirements.forEach(function (r) {
                var li = document.createElement('li');
                li.textContent = r;
                ul.appendChild(li);
            });
            card.appendChild(ul);

            var a = document.createElement('a');
            a.href = job.applyUrl;
            a.target = '_blank';
            a.rel = 'noopener';
            a.className = 'btn-apply';
            a.textContent = 'Postularme →';
            card.appendChild(a);

            container.appendChild(card);
        });
    }

    function buildSearchStr(job) {
        return normalize(
            [job.title, job.company, job.location, job.modality, job.description]
                .concat(job.tags)
                .concat(job.requirements)
                .join(' ')
        );
    }

    searchInput.addEventListener('input', function () {
        var query = normalize(searchInput.value.trim());
        if (!query) { renderJobs(jobs); return; }

        var terms = query.split(/\s+/);
        var filtered = jobs.filter(function (job) {
            var haystack = buildSearchStr(job);
            return terms.every(function (term) { return haystack.indexOf(term) !== -1; });
        });
        renderJobs(filtered);
    });

    renderJobs(jobs);
})();
