document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.querySelector(".nav-toggle");
    const links = document.querySelector(".nav-links");

    if (toggle && links) {
        toggle.addEventListener("click", function () {
            links.classList.toggle("open");
        });
    }

    const languageToggle = document.querySelector("[data-lang-toggle]");
    const languageStorageKey = "aif369-language";
    const supportedLanguages = ["es", "en"];

    const getInitialLanguage = () => {
        const stored = localStorage.getItem(languageStorageKey);
        if (stored && supportedLanguages.includes(stored)) {
            return stored;
        }
        const docLang = document.documentElement.getAttribute("lang");
        return supportedLanguages.includes(docLang) ? docLang : "es";
    };

    const setLanguage = (language) => {
        const lang = supportedLanguages.includes(language) ? language : "es";
        document.documentElement.setAttribute("lang", lang);

        document.querySelectorAll("[data-i18n]").forEach((element) => {
            const attr = element.dataset.i18nAttr;
            if (!element.dataset.i18nEs) {
                const baseValue = attr ? element.getAttribute(attr) : element.textContent;
                element.dataset.i18nEs = baseValue || "";
            }
            const esValue = element.dataset.i18nEs;
            const enValue = element.dataset.i18nEn || esValue;
            const nextValue = lang === "en" ? enValue : esValue;

            if (attr) {
                element.setAttribute(attr, nextValue);
            } else {
                element.textContent = nextValue;
            }
        });

        if (languageToggle) {
            languageToggle.textContent = lang === "es" ? "EN" : "ES";
            languageToggle.setAttribute(
                "aria-label",
                lang === "es" ? "Switch to English" : "Cambiar a español"
            );
        }

        localStorage.setItem(languageStorageKey, lang);
    };

    if (languageToggle) {
        languageToggle.addEventListener("click", () => {
            const current = document.documentElement.getAttribute("lang") || "es";
            setLanguage(current === "es" ? "en" : "es");
        });
    }

    setLanguage(getInitialLanguage());
});
