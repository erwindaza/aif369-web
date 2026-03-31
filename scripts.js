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
    const translations = {
        es: {
            "nav.home": "Inicio",
            "nav.services": "Servicios",
            "nav.education": "Academia",
            "nav.blog": "Insights",
            "nav.author": "Sobre nosotros",
            "nav.scorecard": "Scorecard IA",
            "nav.cta": "Agendar llamada",
            "author.title": "Sobre el autor",
            "author.description": "Conoce al autor detrás de AIF369, su enfoque y experiencia en IA, datos y cloud.",
            "author.subtitle": "Visión, experiencia y enfoque para ayudar a organizaciones a ejecutar IA, datos y cloud con impacto real.",
            "author.name": "Erwin Daza Castillo",
            "author.role": "Founder, AIF369",
            "author.bio1": "Acompaña a equipos ejecutivos en la definición y ejecución de iniciativas de IA, datos y cloud con foco en resultados de negocio, gobernanza y escalabilidad.",
            "author.bio2": "Su trabajo se centra en traducir estrategia en arquitectura, productos de datos y operaciones con métricas claras de impacto.",
            "author.focus.title": "Áreas de enfoque",
            "author.focus.item1": "Gobernanza y estrategia de IA.",
            "author.focus.item2": "Arquitecturas cloud resilientes.",
            "author.focus.item3": "Operación de ML/LLM en producción.",
            "author.cta.title": "¿Quieres conversar?",
            "author.cta.subtitle": "Coordina una conversación para explorar oportunidades y necesidades concretas.",
            "author.cta.button": "Agendar conversación",
            "author.linkedin": "Follow on LinkedIn",
            "author.footer.text": "IA, datos y cloud para la empresa moderna.",
            "nav.scorecard": "Scorecard IA",
            "nav.cta": "Agendar llamada",
            "nav.toggle": "Abrir menú",
            "lang.switch": "EN",
            "lang.switchAria": "Cambiar a inglés",
            "index.title": "AIF369 — Artificial Intelligence Factory | Fábrica de IA, Datos y Cloud",
            "index.description": "AIF369 es una fábrica de inteligencia artificial. Diseñamos, construimos y desplegamos soluciones de IA, datos y cloud que generan resultados reales para empresas.",
            "hero.badge": "Fábrica de IA — Datos — Cloud",
            "hero.title": "Construimos inteligencia artificial para su empresa.",
            "hero.subtitle": "Somos una fábrica de IA: diseñamos, construimos y desplegamos agentes inteligentes, plataformas de datos y arquitecturas cloud que generan ROI medible.",
            "hero.cta.services": "Ver servicios",
            "hero.cta.blog": "Agendar conversación gratuita",
            "hero.note": "De la idea al deploy. Trabajamos con su CIO, CDO, CAIO y equipos de arquitectura para llevar IA a producción.",
            "index.value.title": "Qué fabricamos",
            "index.value.subtitle": "Convertimos ideas de IA en sistemas en producción que generan resultado financiero, cumplimiento regulatorio y ventaja competitiva.",
            "index.value.card1.title": "IA aplicada a procesos reales",
            "index.value.card1.text": "Agentes, modelos y automatizaciones que se integran con sus sistemas actuales - SAP, core bancario, e-commerce, CRM y canales de clientes.",
            "index.value.card2.title": "Plataformas de datos modernas",
            "index.value.card2.text": "Data Lakes, Lakehouse, MLOps y real time streaming con gobernanza activa, catálogo de datos y trazabilidad de extremo a extremo.",
            "index.value.card3.title": "Cloud empresarial",
            "index.value.card3.text": "Arquitecturas en AWS, GCP y Azure con prácticas de ingeniería de alto estándar, CI/CD, observabilidad y seguridad desde el diseño.",
            "index.industries.title": "Industrias donde trabajamos",
            "index.industries.subtitle": "Adaptamos un mismo lenguaje de arquitectura y datos a contextos de negocio muy distintos.",
            "index.industries.fintech": "FinTech y banca",
            "index.industries.retail": "Retail y e-commerce",
            "index.industries.health": "Salud y seguros",
            "index.industries.manufacturing": "Manufactura",
            "index.industries.telecom": "Telecom",
            "index.industries.financial": "Servicios financieros",
            "index.content.title": "Contenido para líderes",
            "index.content.subtitle": "Artículos, guías y modelos para CAIO, CIO, CDO y equipos ejecutivos que toman decisiones sobre IA.",
            "index.content.featured.title": "Insight destacado",
            "index.content.featured.tag": "Artículo",
            "index.content.featured.headline": "2026: cuando la IA deja de asistir y empieza a decidir",
            "index.content.featured.text": "Qué significa que la IA empiece a tomar decisiones operativas en vez de solo asistir a las personas, y cómo deben adaptarse los modelos de gobierno, riesgo y compliance.",
            "index.content.featured.link": "Leer artículo",
            "index.content.academy.title": "Academia AIF369",
            "index.content.academy.text": "Una línea editorial que combina práctica de campo, estándares de arquitectura y marcos de gobierno de IA. Ideal para equipos de datos, arquitectura y transformación digital.",
            "index.content.academy.item1": "Guías prácticas para implementar agentes en producción.",
            "index.content.academy.item2": "Patrones de arquitecturas de datos y ML en la nube.",
            "index.content.academy.item3": "Plantillas para comités de IA y documentación CAIO.",
            "index.content.academy.link": "Ver contenido educativo",
            "index.cta.title": "Conversemos sobre su próximo paso en IA",
            "index.cta.subtitle": "30 minutos para entender su contexto y recomendarle la ruta más rápida para generar valor con IA, datos o cloud.",
            "index.form.name": "Nombre y apellido",
            "index.form.email": "Email corporativo",
            "index.form.role": "Cargo o rol",
            "index.form.context": "Contexto breve de su interés en IA, datos o cloud",
            "index.form.button": "Solicitar conversación",
            "form.success": "Gracias, recibimos tu solicitud. Te contactaremos en menos de 24 horas.",
            "form.error": "No pudimos enviar tu solicitud. Intenta nuevamente o escríbenos a edaza@aif369.com.",
            "index.cta.includes": "¿Qué incluye la conversación?",
            "index.cta.item1": "Radiografía rápida de su situación actual.",
            "index.cta.item2": "Identificación de oportunidades de alto impacto.",
            "index.cta.item3": "Recomendación del servicio ideal según su situación.",
            "index.cta.item4": "Siguiente paso claro y sin compromisos.",
            "index.cta.note": "Sin costo, sin compromiso. Si no somos los indicados, se lo diremos con honestidad.",
            "index.footer.text": "Artificial Intelligence Factory. AIF369 SpA — Chile.",
            "services.title": "Servicios AIF369 - IA, Datos y Cloud",
            "services.description": "Servicios de AIF369 para implementar IA, plataformas de datos y arquitecturas cloud en empresas y corporaciones.",
            "services.header.title": "Servicios AIF369",
            "services.header.subtitle": "Trabajamos con un modelo simple: equipos senior de IA, datos y cloud que se integran con su organización por sprints o tramos de proyecto.",
            "services.card1.title": "Diagnóstico de IA y datos",
            "services.card1.text": "Desde 5 días o hasta 3 semanas: identifique oportunidades de alto impacto y trace un roadmap concreto.",
            "services.card1.item1": "Express (5-7 días): quick wins y arquitectura objetivo.",
            "services.card1.item2": "Ejecutivo (2-3 semanas): evaluación profunda y ROI.",
            "services.card1.item3": "Roadmap priorizado de corto y mediano plazo.",
            "services.card2.title": "Implementación de casos",
            "services.card2.text": "Equipos de proyecto que construyen y ponen en producción soluciones de IA, datos y automatización.",
            "services.card2.item1": "Agentes y copilotos para clientes y backoffice.",
            "services.card2.item2": "Plataformas de datos listas para IA y analítica.",
            "services.card2.item3": "Integración con sistemas existentes y seguridad corporativa.",
            "services.card3.title": "Gobierno y CAIO as a Service",
            "services.card3.text": "Acompañamiento para crear comités, políticas y modelos operativos de IA sin frenar la innovación.",
            "services.card3.item1": "Diseño del rol CAIO y comité de IA.",
            "services.card3.item2": "Políticas de uso responsable y gestión de riesgo.",
            "services.card3.item3": "Modelo de priorización de casos de uso.",
            "services.mlops.title": "MLOps y LLMOps",
            "services.mlops.body1": "Las organizaciones que lideran el camino de la innovación en el aprendizaje automático (ML) y el modelo de lenguaje grande (LLM) se posicionan para obtener una ventaja competitiva significativa. Pero con demasiada frecuencia, llevar las innovaciones de IA más allá de la prueba de concepto y a la producción es una lucha.",
            "services.mlops.body2": "Nuestros servicios MLOps y LLMOps combinan metodologías de Agilismo, Data Mesh y entrega continua para agilizar y acelerar el desarrollo, la implementación y las operaciones de ML y de IA generativa. A través de nuestras asociaciones con proveedores líderes en la nube, te ayudamos a crear soluciones MLOps y LLMOps flexibles y escalables que minimizan el trabajo manual y facilitan ciclos de innovación rápidos para un tiempo de obtención de valor más rápido.",
            "services.mlops.cta": "Ponte en contacto con nosotros",
            "services.latamgpt.title": "Latam GPT",
            "services.latamgpt.body1": "Latam GPT acaba de ser lanzado desde Chile para el mundo, con foco en el español latino y necesidades regionales.",
            "services.latamgpt.body2": "Te ayudamos a explorar casos de uso, integración en procesos de negocio y operación segura con gobernanza y cumplimiento.",
            "services.latamgpt.cta": "Conversemos sobre Latam GPT",
            "services.capabilities.title": "Capacidades técnicas",
            "services.capabilities.subtitle": "Trabajamos con un conjunto de tecnologías que cubre todo el ciclo de vida de datos e IA.",
            "services.capabilities.data": "Datos",
            "services.capabilities.data.text": "Data lakes, lakehouse, orquestación y streaming.",
            "services.capabilities.data.tools": "Spark, Kafka, Airflow, DBT, BigQuery, Redshift, Snowflake, PostgreSQL, NoSQL.",
            "services.capabilities.ai": "IA",
            "services.capabilities.ai.text": "Modelos clásicos, LLMs, agentes, RAG y MLOps.",
            "services.capabilities.ai.tools": "Vertex AI, Bedrock, OpenAI, LangChain, MLflow, Feast, herramientas de evaluación.",
            "services.capabilities.cloud": "Cloud",
            "services.capabilities.cloud.text": "Arquitecturas multi cloud resilientes y seguras.",
            "services.capabilities.cloud.tools": "AWS, GCP, Azure, Kubernetes, Cloud Run, ECS, Terraform, CI/CD.",
            "services.footer.text": "IA, datos y cloud para la empresa moderna.",
            "education.title": "Educación AIF369 - Academia de IA, Datos y Cloud",
            "education.description": "Academia AIF369 con material educativo, guías y recursos prácticos para equipos de IA, datos y cloud.",
            "education.header.title": "Academia AIF369",
            "education.header.subtitle": "Un espacio educativo orientado a la práctica, donde compartimos lo que usamos realmente en proyectos de IA, datos y cloud.",
            "education.card1.title": "Guías prácticas",
            "education.card1.item1": "Checklist para llevar un piloto de IA a producción.",
            "education.card1.item2": "Pasos mínimos para un comité de IA efectivo.",
            "education.card1.item3": "Cómo conectar datos, IA y negocio en un mismo mapa.",
            "education.card1.link": "Solicitar guía",
            "education.card2.title": "Curso profesional: Desarrollo con IA",
            "education.card2.text": "Arquitectura y setup profesional usando Codex AI → GitHub → Vercel, con prácticas reales de despliegue.",
            "education.card2.item1": "Estructura de repositorio, CI/CD y entornos.",
            "education.card2.item2": "Automatización de revisión y control de calidad.",
            "education.card2.item3": "Entrega continua con monitoreo y rollback.",
            "education.card2.link": "Coordinar curso",
            "education.card3.title": "Material para CAIO y comités",
            "education.card3.text": "Plantillas, matrices y esquemas para documentar decisiones de IA y gestionar riesgo sin apagar la innovación.",
            "education.card3.link": "Solicitar material",
            "education.cta.title": "¿Necesitas formación o coaching?",
            "education.cta.subtitle": "Agenda una conversación y diseñamos una propuesta adaptada a tu equipo.",
            "education.cta.button": "Agendar conversación",
            "education.footer.text": "IA, datos y cloud para la empresa moderna.",
            "blog.title": "Blog AIF369 - IA, Datos y Cloud",
            "blog.description": "Blog de AIF369 con análisis y contenidos de vanguardia sobre inteligencia artificial, datos y cloud para ejecutivos y equipos técnicos.",
            "blog.header.title": "Blog AIF369",
            "blog.header.subtitle": "Briefings ejecutivos y marcos accionables para CAIO, CIO, CDO y líderes que necesitan impacto medible.",
            "blog.post1.tag": "Estrategia de IA",
            "blog.post1.title": "2026: cuando la IA deja de asistir y empieza a decidir",
            "blog.post1.meta": "Lectura de 10 minutos - Briefing ejecutivo",
            "blog.post1.text": "Qué ocurre cuando los agentes y modelos empiezan a tomar decisiones operativas, y qué deben cambiar el CAIO, el CIO y los equipos de riesgo para gobernarlas.",
            "blog.post1.link": "Leer artículo completo",
            "blog.post2.tag": "Arquitectura de datos",
            "blog.post2.title": "De data lake a plataforma de decisiones - una ruta práctica",
            "blog.post2.meta": "Próximamente - En revisión editorial",
            "blog.post2.text": "Este análisis estará disponible pronto con ejemplos y marcos prácticos para líderes de datos.",
            "blog.post2.link": "Disponible pronto",
            "blog.aside.title": "Para quién escribimos",
            "blog.aside.text": "CAIO, CIO, CDO, CTO, CEOs y líderes de transformación que necesitan convertir IA en resultados trazables.",
            "blog.aside2.title": "Recibir próximos artículos",
            "blog.aside2.text": "Regístrate para recibir alertas ejecutivas, benchmarks y playbooks cada mes.",
            "blog.footer.text": "IA, datos y cloud para la empresa moderna.",
            "portfolio.title": "Portafolio AIF369 - Casos y demos",
            "portfolio.description": "Portafolio de AIF369 con ejemplos de soluciones de IA, datos y cloud y demos conceptuales.",
            "portfolio.header.title": "Portafolio y demos",
            "portfolio.header.subtitle": "Ejemplos de cómo se ve IA y datos funcionando en escenarios reales.",
            "portfolio.card1.title": "Motor de revisión de catálogos de productos",
            "portfolio.card1.text": "Pipeline que integra datos de múltiples fuentes, ejecuta modelos de calidad de datos y envía alertas a equipos de catálogo.",
            "portfolio.card1.note": "Incluye integración con APIs de terceros, orquestación y monitoreo.",
            "portfolio.card2.title": "Agente para atención en canales digitales",
            "portfolio.card2.text": "Un agente conectado a datos de clientes y productos, capaz de responder, derivar y generar tickets con contexto.",
            "portfolio.card2.note": "Diseñado para operar con políticas de seguridad y cumplimiento de datos personales.",
            "portfolio.card3.title": "Panel de gobierno de IA",
            "portfolio.card3.text": "Tablero donde CAIO y comités pueden ver modelos, datos, riesgos, responsables y estado de cada iniciativa.",
            "portfolio.card3.note": "Enlazado a artefactos técnicos para tener una vista única de la arquitectura viva.",
            "portfolio.note": "Este portafolio se irá actualizando con demos públicas y versiones anonimizadas de proyectos reales.",
            "portfolio.footer.text": "IA, datos y cloud para la empresa moderna.",
            "product.title": "Producto IA AIF369 - AI Governance Starter Kit",
            "product.description": "Producto digital de AIF369 para acelerar gobierno de IA con diagnóstico, plantillas y roadmap ejecutivo.",
            "product.header.title": "AI Governance Starter Kit",
            "product.header.subtitle": "Un producto digital para equipos ejecutivos que necesitan gobernanza de IA sin frenar la innovación.",
            "product.value.title": "Qué incluye el kit",
            "product.value.card1.title": "Diagnóstico express",
            "product.value.card1.text": "Cuestionario ejecutivo + análisis de brechas en gobierno, datos y riesgo en menos de 10 días.",
            "product.value.card2.title": "Plantillas listas",
            "product.value.card2.text": "Políticas de IA responsable, matriz de riesgos, checklist de cumplimiento y comité CAIO.",
            "product.value.card3.title": "Roadmap accionable",
            "product.value.card3.text": "Plan de 90 días con quick wins y prioridades para ejecutar casos de IA con ROI.",
            "product.deliverables.title": "Entregables",
            "product.deliverables.item1": "Informe ejecutivo (PDF) con hallazgos y prioridades.",
            "product.deliverables.item2": "Repositorio de plantillas editables (Docs/Sheets).",
            "product.deliverables.item3": "Sesión de 90 minutos con líderes para alinear el plan.",
            "product.engagement.title": "Opciones de implementación",
            "product.engagement.subtitle": "Definimos el alcance según la madurez actual y el nivel de urgencia del comité ejecutivo.",
            "product.engagement.card1.title": "Sprint ejecutivo",
            "product.engagement.card1.text": "Enfoque rápido para mapear riesgos, priorizar casos y alinear al CAIO con el negocio.",
            "product.engagement.card1.item1": "Workshops con líderes y dueños de datos.",
            "product.engagement.card1.item2": "Mapa de riesgos y quick wins.",
            "product.engagement.card1.item3": "Plan de 90 días para habilitar gobernanza.",
            "product.engagement.card2.title": "Acompañamiento enterprise",
            "product.engagement.card2.text": "Diseñado para organizaciones con varias unidades que necesitan estandarizar gobierno y ejecución.",
            "product.engagement.card2.item1": "Diagnóstico por unidad y comité de IA.",
            "product.engagement.card2.item2": "Plantillas adaptadas por industria.",
            "product.engagement.card2.item3": "Gobernanza continua y métricas ejecutivas.",
            "product.cta.title": "Solicitar el kit",
            "product.cta.subtitle": "Escríbenos para recibir el detalle completo y coordinar fechas.",
            "product.cta.button": "Quiero el AI Governance Starter Kit",
            "book.title": "Libro: AI Modernization & MLOps Leadership",
            "book.subtitle": "Contenido premium para líderes que necesitan llevar IA y LLMs a producción con gobernanza, seguridad y cumplimiento.",
            "book.item1": "Arquitectura y operación de MLOps/LLMOps para proyectos reales.",
            "book.item2": "Guías prácticas para gobernanza, riesgo y trazabilidad.",
            "book.item3": "Alineación con marcos regulatorios (EU AI Act y normativas emergentes en Chile/Latam).",
            "book.cta": "Adquirir el libro",
            "product.footer.text": "Producto digital de AIF369 para acelerar gobierno de IA.",
            "post.title": "Artículo en desarrollo - Blog AIF369",
            "post.description": "Artículo en desarrollo para el blog de AIF369 sobre IA, datos y cloud.",
            "post.tag": "En desarrollo",
            "post.header": "Artículo en preparación",
            "post.meta": "Contenido en edición - Disponible pronto.",
            "post.intro": "Estamos preparando este análisis con ejemplos reales, marcos de decisión y aprendizajes de proyectos recientes.",
            "post.section1": "Qué encontrarás aquí",
            "post.section1.text": "Un resumen ejecutivo, decisiones clave y recomendaciones para líderes de datos e IA.",
            "post.section2": "Fecha estimada",
            "post.section2.item1": "Entrega editorial en las próximas semanas.",
            "post.section2.item2": "Incluye checklist y plantillas descargables.",
            "post.section2.item3": "Disponible en español e inglés.",
            "post.section3": "¿Necesitas este contenido antes?",
            "post.section3.text": "Escríbenos y comparte tu caso para priorizar el contenido o recibir un resumen ejecutivo.",
            "post.back": "Volver al blog",
            "post.footer.text": "IA, datos y cloud para la empresa moderna.",
            "article.title": "2026: cuando la IA deja de asistir y empieza a decidir - Blog AIF369",
            "article.description": "Análisis sobre el momento en que la IA empieza a tomar decisiones operativas y los cambios de gobierno, riesgo y arquitectura que esto exige.",
            "article.tag": "Estrategia de IA",
            "article.header": "2026: cuando la IA deja de asistir y empieza a decidir",
            "article.meta": "Lectura de 10 minutos - Para CAIO, CIO, CDO y equipos de arquitectura.",
            "article.intro": "Durante años hablamos de inteligencia artificial como un asistente. El punto de inflexión llega cuando los modelos y agentes empiezan a ejecutar decisiones sobre clientes, procesos y recursos.",
            "article.section1": "De \"asistente\" a \"operador\"",
            "article.section1.text": "El paso de IA asistiva a IA operativa no se da por marketing sino por diseño de procesos. Un asistente propone, un operador ejecuta. El impacto en riesgo, cumplimiento y gobierno de datos es inmediato.",
            "article.section2": "Qué cambia para el CAIO y el comité de IA",
            "article.section2.item1": "La conversación pasa de \"qué podemos automatizar\" a \"qué estamos dispuestos a dejar en manos de un sistema\".",
            "article.section2.item2": "Se hace evidente la necesidad de trazabilidad exhaustiva sobre datos, modelos, prompts y decisiones.",
            "article.section2.item3": "Los incidentes dejan de ser solo técnicos y pasan a ser reputacionales y regulatorios.",
            "article.section3": "Tres decisiones clave antes de delegar decisiones en IA",
            "article.section3.item1": "Definir qué decisiones no pueden ser delegadas en ningún caso, aunque exista capacidad técnica.",
            "article.section3.item2": "Establecer niveles de autonomía por tipo de proceso, con límites claros y supervisión activa.",
            "article.section3.item3": "Diseñar la observabilidad del sistema como un requisito desde el inicio, no como un agregado posterior.",
            "article.section4": "Cerrar la brecha entre arquitectura y gobierno",
            "article.section4.text": "La empresa que llegue sólida a este escenario no será la que más modelos tenga en producción, sino la que alinee arquitectura, datos y gobierno en un lenguaje operativo común.",
            "article.cta": "En AIF369 diseñamos esa línea entre asistencia y decisión, y construimos la arquitectura, procesos y comités que permiten escalar IA sin frenar la innovación.",
            "article.back": "Volver al blog",
            "article.footer.text": "IA, datos y cloud para la empresa moderna."
        },
        en: {
            "nav.home": "Home",
            "nav.services": "Services",
            "nav.education": "Academy",
            "nav.blog": "Insights",
            "nav.author": "About us",
            "nav.scorecard": "AI Scorecard",
            "nav.cta": "Book a call",
            "author.title": "About the author",
            "author.description": "Meet the author behind AIF369 and his focus on AI, data, and cloud.",
            "author.subtitle": "Vision, experience, and focus to help organizations execute AI, data, and cloud with real impact.",
            "author.name": "Erwin Daza Castillo",
            "author.role": "Founder, AIF369",
            "author.bio1": "He supports executive teams in defining and executing AI, data, and cloud initiatives focused on business outcomes, governance, and scalability.",
            "author.bio2": "His work focuses on translating strategy into architecture, data products, and operations with clear impact metrics.",
            "author.focus.title": "Focus areas",
            "author.focus.item1": "AI governance and strategy.",
            "author.focus.item2": "Resilient cloud architectures.",
            "author.focus.item3": "Production ML/LLM operations.",
            "author.cta.title": "Want to talk?",
            "author.cta.subtitle": "Schedule a conversation to explore concrete opportunities and needs.",
            "author.cta.button": "Schedule a conversation",
            "author.linkedin": "Follow on LinkedIn",
            "author.footer.text": "AI, data, and cloud for the modern enterprise.",
            "nav.scorecard": "AI Scorecard",
            "nav.cta": "Book a call",
            "nav.toggle": "Open menu",
            "lang.switch": "ES",
            "lang.switchAria": "Switch to Spanish",
            "index.title": "AIF369 — Artificial Intelligence Factory | AI, Data & Cloud",
            "index.description": "AIF369 is an Artificial Intelligence Factory. We design, build, and deploy AI, data, and cloud solutions that deliver real results for enterprises.",
            "hero.badge": "AI Factory — Data — Cloud",
            "hero.title": "We build artificial intelligence for your business.",
            "hero.subtitle": "We are an AI factory: we design, build, and deploy intelligent agents, data platforms, and cloud architectures that deliver measurable ROI.",
            "hero.cta.services": "View services",
            "hero.cta.blog": "Book a free call",
            "hero.note": "From idea to deploy. We work with your CIO, CDO, CAIO, and architecture teams to take AI to production.",
            "index.value.title": "What we build",
            "index.value.subtitle": "We turn AI ideas into production systems that drive financial results, regulatory compliance, and competitive advantage.",
            "index.value.card1.title": "AI applied to real processes",
            "index.value.card1.text": "Agents, models, and automations that integrate with your existing systems - SAP, core banking, e-commerce, CRM, and customer channels.",
            "index.value.card2.title": "Modern data platforms",
            "index.value.card2.text": "Data lakes, lakehouse, MLOps, and real-time streaming with active governance, data cataloging, and end-to-end lineage.",
            "index.value.card3.title": "Enterprise cloud",
            "index.value.card3.text": "Architectures on AWS, GCP, and Azure with high-standard engineering practices, CI/CD, observability, and security by design.",
            "index.industries.title": "Industries we serve",
            "index.industries.subtitle": "We adapt a shared architecture and data language to very different business contexts.",
            "index.industries.fintech": "FinTech and banking",
            "index.industries.retail": "Retail and e-commerce",
            "index.industries.health": "Health and insurance",
            "index.industries.manufacturing": "Manufacturing",
            "index.industries.telecom": "Telecom",
            "index.industries.financial": "Financial services",
            "index.content.title": "Content for leaders",
            "index.content.subtitle": "Articles, guides, and models for CAIO, CIO, CDO, and executive teams making AI decisions.",
            "index.content.featured.title": "Featured insight",
            "index.content.featured.tag": "Article",
            "index.content.featured.headline": "2026: when AI stops assisting and starts deciding",
            "index.content.featured.text": "What it means for AI to start making operational decisions instead of only assisting people, and how governance, risk, and compliance models must adapt.",
            "index.content.featured.link": "Read article",
            "index.content.academy.title": "AIF369 Academy",
            "index.content.academy.text": "An editorial line that blends field practice, architecture standards, and AI governance frameworks. Ideal for data, architecture, and digital transformation teams.",
            "index.content.academy.item1": "Practical guides to deploy agents in production.",
            "index.content.academy.item2": "Data and ML architecture patterns in the cloud.",
            "index.content.academy.item3": "Templates for AI committees and CAIO documentation.",
            "index.content.academy.link": "See education content",
            "index.cta.title": "Let's talk about your next AI step",
            "index.cta.subtitle": "A 30-minute conversation to understand your current state and outline action paths.",
            "index.form.name": "Full name",
            "index.form.email": "Corporate email",
            "index.form.role": "Title or role",
            "index.form.context": "Brief context about your interest in AI, data, or cloud",
            "index.form.button": "Request conversation",
            "form.success": "Thanks! We received your request and will contact you within 24 hours.",
            "form.error": "We could not send your request. Please try again or email edaza@aif369.com.",
            "index.cta.includes": "What you get",
            "index.cta.item1": "Quick assessment of your current AI and data capabilities.",
            "index.cta.item2": "Map of high-impact opportunities for your industry.",
            "index.cta.item3": "Recommendation for the right service based on your situation.",
            "index.cta.item4": "Clear, no-obligation next-step proposal.",
            "index.cta.note": "No cost, no commitment. A focused session on strategic and technical clarity.",
            "index.footer.text": "Artificial Intelligence Factory. AIF369 SpA — Chile.",
            "services.title": "AIF369 Services - AI, Data & Cloud",
            "services.description": "AIF369 services to implement AI, data platforms, and cloud architectures for enterprises and corporations.",
            "services.header.title": "AIF369 Services",
            "services.header.subtitle": "We work with a simple model: senior AI, data, and cloud teams that integrate with your organization in sprints or project phases.",
            "services.card1.title": "AI & Data Assessment",
            "services.card1.text": "From 5 days or up to 3 weeks: identify high-impact opportunities and build a concrete roadmap.",
            "services.card1.item1": "Express (5-7 days): quick wins and target architecture.",
            "services.card1.item2": "Executive (2-3 weeks): deep assessment and ROI.",
            "services.card1.item3": "Prioritized short- and mid-term roadmap.",
            "services.card2.title": "Use-case delivery",
            "services.card2.text": "Project teams that build and launch AI, data, and automation solutions into production.",
            "services.card2.item1": "Agents and copilots for customers and back office.",
            "services.card2.item2": "Data platforms ready for AI and analytics.",
            "services.card2.item3": "Integration with existing systems and corporate security.",
            "services.card3.title": "Governance and CAIO as a Service",
            "services.card3.text": "Support to create committees, policies, and AI operating models without slowing innovation.",
            "services.card3.item1": "Design of the CAIO role and AI committee.",
            "services.card3.item2": "Responsible use policies and risk management.",
            "services.card3.item3": "Use-case prioritization model.",
            "services.mlops.title": "MLOps & LLMOps",
            "services.mlops.body1": "Organizations leading innovation in machine learning (ML) and large language models (LLMs) position themselves for significant competitive advantage. But too often, taking AI innovations beyond proof of concept and into production is a struggle.",
            "services.mlops.body2": "Our MLOps and LLMOps services combine Agile, Data Mesh, and continuous delivery practices to streamline and accelerate ML and generative AI development, deployment, and operations. Through partnerships with leading cloud providers, we help you build flexible and scalable MLOps/LLMOps solutions that minimize manual work and enable rapid innovation cycles for faster time to value.",
            "services.mlops.cta": "Contact us",
            "services.latamgpt.title": "Latam GPT",
            "services.latamgpt.body1": "Latam GPT was recently launched from Chile to the world, focused on Latin American Spanish and regional needs.",
            "services.latamgpt.body2": "We help you explore use cases, business process integration, and safe operations with governance and compliance.",
            "services.latamgpt.cta": "Let’s talk about Latam GPT",
            "services.capabilities.title": "Technical capabilities",
            "services.capabilities.subtitle": "We work with a technology stack that covers the full data and AI lifecycle.",
            "services.capabilities.data": "Data",
            "services.capabilities.data.text": "Data lakes, lakehouse, orchestration, and streaming.",
            "services.capabilities.data.tools": "Spark, Kafka, Airflow, DBT, BigQuery, Redshift, Snowflake, PostgreSQL, NoSQL.",
            "services.capabilities.ai": "AI",
            "services.capabilities.ai.text": "Traditional models, LLMs, agents, RAG, and MLOps.",
            "services.capabilities.ai.tools": "Vertex AI, Bedrock, OpenAI, LangChain, MLflow, Feast, evaluation tools.",
            "services.capabilities.cloud": "Cloud",
            "services.capabilities.cloud.text": "Resilient and secure multi-cloud architectures.",
            "services.capabilities.cloud.tools": "AWS, GCP, Azure, Kubernetes, Cloud Run, ECS, Terraform, CI/CD.",
            "services.footer.text": "AI, data, and cloud for the modern enterprise.",
            "education.title": "AIF369 Education - AI, Data & Cloud Academy",
            "education.description": "AIF369 Academy with educational material, guides, and practical resources for AI, data, and cloud teams.",
            "education.header.title": "AIF369 Academy",
            "education.header.subtitle": "A practice-oriented learning space where we share what we actually use in AI, data, and cloud projects.",
            "education.card1.title": "Practical guides",
            "education.card1.item1": "Checklist to move an AI pilot into production.",
            "education.card1.item2": "Minimum steps for an effective AI committee.",
            "education.card1.item3": "How to connect data, AI, and business in one map.",
            "education.card1.link": "Request guide",
            "education.card2.title": "Professional course: AI development",
            "education.card2.text": "Professional architecture and setup using Codex AI → GitHub → Vercel, with real deployment practices.",
            "education.card2.item1": "Repository structure, CI/CD, and environments.",
            "education.card2.item2": "Automated reviews and quality gates.",
            "education.card2.item3": "Continuous delivery with monitoring and rollback.",
            "education.card2.link": "Plan training",
            "education.card3.title": "Materials for CAIOs and committees",
            "education.card3.text": "Templates, matrices, and frameworks to document AI decisions and manage risk without shutting down innovation.",
            "education.card3.link": "Request material",
            "education.cta.title": "Need training or coaching?",
            "education.cta.subtitle": "Schedule a conversation and we will tailor a proposal for your team.",
            "education.cta.button": "Schedule a conversation",
            "education.footer.text": "AI, data, and cloud for the modern enterprise.",
            "blog.title": "AIF369 Blog - AI, Data & Cloud",
            "blog.description": "AIF369 blog with cutting-edge analysis and content on artificial intelligence, data, and cloud for executives and technical teams.",
            "blog.header.title": "AIF369 Blog",
            "blog.header.subtitle": "Executive briefings and actionable frameworks for CAIOs, CIOs, CDOs, and leaders who need measurable impact.",
            "blog.post1.tag": "AI strategy",
            "blog.post1.title": "2026: when AI stops assisting and starts deciding",
            "blog.post1.meta": "10-minute read - Executive briefing",
            "blog.post1.text": "What happens when agents and models start making operational decisions, and what CAIOs, CIOs, and risk teams must change to govern them.",
            "blog.post1.link": "Read full article",
            "blog.post2.tag": "Data architecture",
            "blog.post2.title": "From data lake to decision platform - a practical path",
            "blog.post2.meta": "Coming soon - Editorial review",
            "blog.post2.text": "This analysis will be available soon with examples and practical frameworks for data leaders.",
            "blog.post2.link": "Available soon",
            "blog.aside.title": "Who we write for",
            "blog.aside.text": "CAIOs, CIOs, CDOs, CTOs, CEOs, and transformation leaders who need to turn AI into traceable results.",
            "blog.aside2.title": "Get upcoming articles",
            "blog.aside2.text": "Subscribe to receive executive alerts, benchmarks, and playbooks each month.",
            "blog.footer.text": "AI, data, and cloud for the modern enterprise.",
            "portfolio.title": "AIF369 Portfolio - Cases & Demos",
            "portfolio.description": "AIF369 portfolio with examples of AI, data, and cloud solutions and conceptual demos.",
            "portfolio.header.title": "Portfolio and demos",
            "portfolio.header.subtitle": "Examples of what AI and data look like in real scenarios.",
            "portfolio.card1.title": "Product catalog review engine",
            "portfolio.card1.text": "Pipeline that integrates data from multiple sources, runs data quality models, and sends alerts to catalog teams.",
            "portfolio.card1.note": "Includes third-party API integration, orchestration, and monitoring.",
            "portfolio.card2.title": "Agent for digital channel support",
            "portfolio.card2.text": "An agent connected to customer and product data, able to respond, route, and create tickets with context.",
            "portfolio.card2.note": "Designed to operate with security policies and personal data compliance.",
            "portfolio.card3.title": "AI governance dashboard",
            "portfolio.card3.text": "Dashboard where CAIOs and committees can see models, data, risks, owners, and status of each initiative.",
            "portfolio.card3.note": "Linked to technical artifacts for a single view of the living architecture.",
            "portfolio.note": "This portfolio will be updated with public demos and anonymized versions of real projects.",
            "portfolio.footer.text": "AI, data, and cloud for the modern enterprise.",
            "product.title": "AIF369 AI Product - AI Governance Starter Kit",
            "product.description": "AIF369 digital product to accelerate AI governance with diagnosis, templates, and executive roadmap.",
            "product.header.title": "AI Governance Starter Kit",
            "product.header.subtitle": "A digital product for executive teams that need AI governance without slowing innovation.",
            "product.value.title": "What’s included",
            "product.value.card1.title": "Express assessment",
            "product.value.card1.text": "Executive questionnaire + gap analysis across governance, data, and risk in under 10 days.",
            "product.value.card2.title": "Ready templates",
            "product.value.card2.text": "Responsible AI policies, risk matrix, compliance checklist, and CAIO committee templates.",
            "product.value.card3.title": "Actionable roadmap",
            "product.value.card3.text": "90-day plan with quick wins and priorities to execute AI use cases with ROI.",
            "product.deliverables.title": "Deliverables",
            "product.deliverables.item1": "Executive report (PDF) with findings and priorities.",
            "product.deliverables.item2": "Editable template repository (Docs/Sheets).",
            "product.deliverables.item3": "90-minute alignment session with leaders.",
            "product.engagement.title": "Implementation options",
            "product.engagement.subtitle": "We set scope based on current maturity and the executive committee’s urgency.",
            "product.engagement.card1.title": "Executive sprint",
            "product.engagement.card1.text": "Fast track to map risks, prioritize use cases, and align the CAIO with the business.",
            "product.engagement.card1.item1": "Workshops with leaders and data owners.",
            "product.engagement.card1.item2": "Risk map and quick wins.",
            "product.engagement.card1.item3": "90-day plan to enable governance.",
            "product.engagement.card2.title": "Enterprise partnership",
            "product.engagement.card2.text": "Designed for multi-unit organizations that need standardized governance and execution.",
            "product.engagement.card2.item1": "Unit-level diagnostics and AI committee setup.",
            "product.engagement.card2.item2": "Industry-tailored templates.",
            "product.engagement.card2.item3": "Ongoing governance and executive metrics.",
            "product.cta.title": "Request the kit",
            "product.cta.subtitle": "Contact us to receive the full details and schedule dates.",
            "product.cta.button": "I want the AI Governance Starter Kit",
            "book.title": "Book: AI Modernization & MLOps Leadership",
            "book.subtitle": "Premium content for leaders who need to take AI and LLMs to production with governance, security, and compliance.",
            "book.item1": "MLOps/LLMOps architecture and operations for real projects.",
            "book.item2": "Practical guides for governance, risk, and traceability.",
            "book.item3": "Alignment with regulatory frameworks (EU AI Act and emerging rules in Chile/Latam).",
            "book.cta": "Buy the book",
            "product.footer.text": "AIF369 digital product to accelerate AI governance.",
            "post.title": "Article in progress - AIF369 Blog",
            "post.description": "In-progress article for the AIF369 blog about AI, data, and cloud.",
            "post.tag": "In progress",
            "post.header": "Article in preparation",
            "post.meta": "Editing in progress - Available soon.",
            "post.intro": "We are preparing this analysis with real examples, decision frameworks, and learnings from recent projects.",
            "post.section1": "What you’ll find here",
            "post.section1.text": "An executive summary, key decisions, and recommendations for data and AI leaders.",
            "post.section2": "Estimated timing",
            "post.section2.item1": "Editorial delivery in the next few weeks.",
            "post.section2.item2": "Includes a checklist and downloadable templates.",
            "post.section2.item3": "Available in Spanish and English.",
            "post.section3": "Need this sooner?",
            "post.section3.text": "Reach out and share your case to prioritize this content or receive an executive summary.",
            "post.back": "Back to blog",
            "post.footer.text": "AI, data, and cloud for the modern enterprise.",
            "article.title": "2026: when AI stops assisting and starts deciding - AIF369 Blog",
            "article.description": "Analysis of the moment when AI starts making operational decisions and the governance, risk, and architecture changes this requires.",
            "article.tag": "AI strategy",
            "article.header": "2026: when AI stops assisting and starts deciding",
            "article.meta": "10-minute read - For CAIOs, CIOs, CDOs, and architecture teams.",
            "article.intro": "For years we talked about artificial intelligence as an assistant. The real inflection point is when models and agents begin to execute decisions about customers, processes, and resources.",
            "article.section1": "From \"assistant\" to \"operator\"",
            "article.section1.text": "The shift from assistive AI to operational AI is not driven by marketing but by process design. An assistant proposes; an operator executes. The impact on risk, compliance, and data governance is immediate.",
            "article.section2": "What changes for the CAIO and the AI committee",
            "article.section2.item1": "The conversation moves from \"what can we automate\" to \"what are we willing to leave in the hands of a system\".",
            "article.section2.item2": "The need for exhaustive traceability across data, models, prompts, and decisions becomes evident.",
            "article.section2.item3": "Incidents stop being purely technical and become reputational and regulatory.",
            "article.section3": "Three key decisions before delegating decisions to AI",
            "article.section3.item1": "Define which decisions can never be delegated, even if the technical capability exists.",
            "article.section3.item2": "Set autonomy levels by process type, with clear limits and active supervision.",
            "article.section3.item3": "Design system observability as a requirement from day one, not an afterthought.",
            "article.section4": "Closing the gap between architecture and governance",
            "article.section4.text": "The company that arrives strong in this scenario won’t be the one with the most models in production, but the one that aligns architecture, data, and governance in a single operating language.",
            "article.cta": "At AIF369 we design that line between assistance and decision, and build the architecture, processes, and committees that let you scale AI without slowing innovation.",
            "article.back": "Back to blog",
            "article.footer.text": "AI, data, and cloud for the modern enterprise."
        }
    };

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
                element.textContent = dictionary[key];
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
        applyTranslations(target);
    }

    if (langToggles.length > 0) {
        langToggles.forEach((langToggle) => {
            langToggle.addEventListener("click", function (event) {
                event.preventDefault();
                event.stopPropagation();
            const current = getCurrentLanguage();
            const next = current === "es" ? "en" : "es";
            setLanguage(next);
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
        const messageParts = [];

        if (submission.message) {
            messageParts.push(submission.message);
        }

        if (submission.role) {
            messageParts.push(`Cargo/rol: ${submission.role}`);
        }

        if (submission.context) {
            messageParts.push(`Contexto: ${submission.context}`);
        }

        if (submission.interest) {
            messageParts.push(`Interés: ${submission.interest}`);
        }

        if (submission.teamSize) {
            messageParts.push(`Tamaño del equipo: ${submission.teamSize}`);
        }

        if (messageParts.length === 0) {
            messageParts.push("Solicitud enviada desde el sitio web.");
        }

        return {
            name: submission.fullName || submission.name || "",
            email: submission.email || "",
            company: submission.company || "",
            interest: submission.interest || "",
            team_size: submission.teamSize || "",
            message: messageParts.join("\n"),
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
            } else {
                setFormState('error');
            }
        });
    });

    setLanguage(getInitialLanguage());
});

/* ═══════════════════════════════════════════════════════════
   ENROLLMENT FORM + PAYPAL SMART BUTTONS
   Flow: Fill form → Validate → Show PayPal → Pay $10 → Success
   ═══════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', function () {
    var wrappers = document.querySelectorAll('.enrollment-wrapper');
    if (!wrappers.length) return;

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

            // Render PayPal buttons (only once)
            if (!paypalRendered && typeof paypal !== 'undefined' && paypal.Buttons) {
                paypalRendered = true;
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
            ? 'https://aif369-backend-api-dev-944757324945.us-central1.run.app'
            : 'https://aif369-backend-api-production-944757324945.us-central1.run.app';

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

            var tagsHtml = job.tags.map(function (t) {
                return '<span class="job-tag">' + t + '</span>';
            }).join('');

            var reqsHtml = job.requirements.map(function (r) {
                return '<li>' + r + '</li>';
            }).join('');

            card.innerHTML =
                '<h3>' + job.title + '</h3>' +
                '<p class="job-meta">' + job.company + ' · ' + job.modality + ' · ' + job.location + '</p>' +
                '<p class="job-desc">' + job.description + '</p>' +
                '<div class="job-tags">' + tagsHtml + '</div>' +
                '<ul style="font-size:0.85rem;color:var(--text-secondary);margin-bottom:var(--space-4);padding-left:20px;line-height:1.8;">' + reqsHtml + '</ul>' +
                '<a href="' + encodeURI(job.applyUrl) + '" target="_blank" rel="noopener" class="btn-apply">Postularme →</a>';

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
