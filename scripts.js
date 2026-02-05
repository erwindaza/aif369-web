document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.querySelector(".nav-toggle");
    const links = document.querySelector(".nav-links");

    if (toggle && links) {
        toggle.setAttribute("aria-expanded", "false");
        toggle.addEventListener("click", function () {
            links.classList.toggle("open");
            const isOpen = links.classList.contains("open");
            toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
        });

        document.addEventListener("click", function (event) {
            if (!links.contains(event.target) && event.target !== toggle) {
                links.classList.remove("open");
                toggle.setAttribute("aria-expanded", "false");
            }
        });

        links.querySelectorAll("a").forEach((link) => {
            link.addEventListener("click", function () {
                links.classList.remove("open");
                toggle.setAttribute("aria-expanded", "false");
            });
        });
    }

    const translations = {
        es: {
            "nav.home": "Inicio",
            "nav.services": "Servicios",
            "nav.education": "Educación",
            "nav.blog": "Blog",
            "nav.portfolio": "Portafolio",
            "nav.product": "Producto IA",
            "nav.diagnosis": "Diagnóstico",
            "nav.toggle": "Abrir menú",
            "lang.switch": "EN",
            "lang.switchAria": "Cambiar a inglés",
            "index.title": "AIF369 - Equipos de IA, Datos y Cloud para Corporaciones",
            "index.description": "AIF369 ofrece equipos senior de IA, datos y cloud para ejecutar proyectos de alto impacto con ROI medible en empresas y corporaciones.",
            "hero.badge": "IA aplicada - Datos vivos - Cloud escalable",
            "hero.title": "Equipos de IA, Datos y Cloud para acelerar su empresa.",
            "hero.subtitle": "Diseñamos y desplegamos arquitecturas modernas, agentes inteligentes y sistemas de datos que generan ROI medible, con foco en gobierno, seguridad y operación continua.",
            "hero.cta.services": "Ver servicios",
            "hero.cta.blog": "Leer el último insight",
            "hero.note": "Hablamos el lenguaje del negocio y el lenguaje técnico. Trabajamos con su CIO, CDO, CAIO y equipos de arquitectura.",
            "index.value.title": "Qué hacemos",
            "index.value.subtitle": "Convertimos ideas de IA en sistemas que generan resultado financiero, cumplimiento regulatorio y ventaja competitiva.",
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
            "index.cta.title": "Agendar diagnóstico ejecutivo",
            "index.cta.subtitle": "Una conversación de 45 minutos para entender el estado actual de su organización y posibles rutas de acción.",
            "index.form.name": "Nombre y apellido",
            "index.form.email": "Email corporativo",
            "index.form.role": "Cargo o rol",
            "index.form.context": "Contexto breve de su interés en IA, datos o cloud",
            "index.form.button": "Solicitar diagnóstico",
            "form.success": "Gracias, recibimos tu solicitud. Te contactaremos pronto.",
            "index.cta.includes": "Qué incluye",
            "index.cta.item1": "Radiografía rápida de capacidades actuales.",
            "index.cta.item2": "Mapa de oportunidades de alto impacto.",
            "index.cta.item3": "Riesgos clave de datos y gobernanza a revisar.",
            "index.cta.item4": "Propuesta de siguiente paso clara y accionable.",
            "index.cta.note": "Sesión ejecutiva enfocada en claridad estratégica y técnica, sin compromisos comerciales.",
            "index.modal.title": "Resumen de solicitud enviada",
            "index.modal.subtitle": "Estos son los datos enviados. Guarda este resumen y revisa dónde se almacenan.",
            "index.modal.nameLabel": "Nombre:",
            "index.modal.emailLabel": "Email:",
            "index.modal.roleLabel": "Cargo:",
            "index.modal.contextLabel": "Contexto:",
            "index.modal.storageNote": "Por ahora los datos quedan guardados localmente en el navegador (storage embebido). Más adelante podemos conectarlo a una base de datos real.",
            "index.modal.emailNote": "Al enviar se abrirá tu cliente de correo para mandar la solicitud a edaza@aif369.com.",
            "index.modal.emailButton": "Enviar email",
            "index.modal.closeButton": "Cerrar",
            "index.modal.closeAria": "Cerrar",
            "index.modal.emailSubject": "Nueva solicitud de diagnóstico ejecutivo",
            "index.modal.emailBodyIntro": "Detalles de la solicitud:",
            "index.footer.text": "IA, datos y cloud para la empresa moderna. AIF369 SpA - Chile.",
            "services.title": "Servicios AIF369 - IA, Datos y Cloud",
            "services.description": "Servicios de AIF369 para implementar IA, plataformas de datos y arquitecturas cloud en empresas y corporaciones.",
            "services.header.title": "Servicios AIF369",
            "services.header.subtitle": "Trabajamos con un modelo simple: equipos senior de IA, datos y cloud que se integran con su organización por sprints o tramos de proyecto.",
            "services.card1.title": "Diagnóstico ejecutivo de IA y datos",
            "services.card1.text": "2 a 3 semanas para entender el punto de partida, identificar oportunidades de alto impacto y estimar ROI.",
            "services.card1.item1": "Entrevistas con líderes y equipos técnicos.",
            "services.card1.item2": "Mapa de capacidades actuales y brechas.",
            "services.card1.item3": "Roadmap de corto y mediano plazo.",
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
            "nav.education": "Education",
            "nav.blog": "Blog",
            "nav.portfolio": "Portfolio",
            "nav.product": "AI Product",
            "nav.diagnosis": "Assessment",
            "nav.toggle": "Open menu",
            "lang.switch": "ES",
            "lang.switchAria": "Switch to Spanish",
            "index.title": "AIF369 - AI, Data & Cloud Teams for Corporations",
            "index.description": "AIF369 provides senior AI, data, and cloud teams to deliver high-impact projects with measurable ROI for enterprises and corporations.",
            "hero.badge": "Applied AI - Living data - Scalable cloud",
            "hero.title": "AI, Data, and Cloud teams to accelerate your business.",
            "hero.subtitle": "We design and deploy modern architectures, intelligent agents, and data systems that deliver measurable ROI, with a focus on governance, security, and continuous operations.",
            "hero.cta.services": "View services",
            "hero.cta.blog": "Read the latest insight",
            "hero.note": "We speak the language of business and the language of technology. We partner with your CIO, CDO, CAIO, and architecture teams.",
            "index.value.title": "What we do",
            "index.value.subtitle": "We turn AI ideas into systems that drive financial results, regulatory compliance, and competitive advantage.",
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
            "index.cta.title": "Schedule an executive assessment",
            "index.cta.subtitle": "A 45-minute conversation to understand your organization’s current state and possible action paths.",
            "index.form.name": "Full name",
            "index.form.email": "Corporate email",
            "index.form.role": "Title or role",
            "index.form.context": "Brief context about your interest in AI, data, or cloud",
            "index.form.button": "Request assessment",
            "form.success": "Thanks, we received your request. We will contact you soon.",
            "index.cta.includes": "What’s included",
            "index.cta.item1": "Rapid snapshot of current capabilities.",
            "index.cta.item2": "Map of high-impact opportunities.",
            "index.cta.item3": "Key data and governance risks to review.",
            "index.cta.item4": "Clear, actionable next-step proposal.",
            "index.cta.note": "An executive session focused on strategic and technical clarity, with no commercial commitments.",
            "index.modal.title": "Submitted request summary",
            "index.modal.subtitle": "These are the details you submitted. Save this summary and review where the data is stored.",
            "index.modal.nameLabel": "Name:",
            "index.modal.emailLabel": "Email:",
            "index.modal.roleLabel": "Title:",
            "index.modal.contextLabel": "Context:",
            "index.modal.storageNote": "For now the data is saved locally in the browser (embedded storage). We can connect this to a real database later.",
            "index.modal.emailNote": "Sending will open your email client to send the request to edaza@aif369.com.",
            "index.modal.emailButton": "Send email",
            "index.modal.closeButton": "Close",
            "index.modal.closeAria": "Close",
            "index.modal.emailSubject": "New executive assessment request",
            "index.modal.emailBodyIntro": "Request details:",
            "index.footer.text": "AI, data, and cloud for the modern enterprise. AIF369 SpA - Chile.",
            "services.title": "AIF369 Services - AI, Data & Cloud",
            "services.description": "AIF369 services to implement AI, data platforms, and cloud architectures for enterprises and corporations.",
            "services.header.title": "AIF369 Services",
            "services.header.subtitle": "We work with a simple model: senior AI, data, and cloud teams that integrate with your organization in sprints or project phases.",
            "services.card1.title": "Executive AI and data assessment",
            "services.card1.text": "2 to 3 weeks to understand the starting point, identify high-impact opportunities, and estimate ROI.",
            "services.card1.item1": "Interviews with leaders and technical teams.",
            "services.card1.item2": "Map of current capabilities and gaps.",
            "services.card1.item3": "Short- and mid-term roadmap.",
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

    const contactForms = document.querySelectorAll("[data-contact-form]");
    const modal = document.querySelector("[data-modal]");
    const modalCloseButtons = document.querySelectorAll("[data-modal-close]");
    const emailLink = document.querySelector("[data-email-link]");

    function closeModal() {
        if (modal) {
            modal.hidden = true;
            document.body.classList.remove("modal-open");
        }
    }

    function openModal() {
        if (modal) {
            modal.hidden = false;
            document.body.classList.add("modal-open");
        }
    }

    closeModal();

    if (modal) {
        modal.addEventListener("click", function (event) {
            if (event.target === modal) {
                closeModal();
            }
        });
    }

    modalCloseButtons.forEach((button) => {
        button.addEventListener("click", closeModal);
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeModal();
        }
    });

    contactForms.forEach((form) => {
        form.addEventListener("submit", async function (event) {
            event.preventDefault();
            const formData = new FormData(form);
            const submission = {
                fullName: formData.get("fullName")?.toString().trim() || "",
                email: formData.get("email")?.toString().trim() || "",
                role: formData.get("role")?.toString().trim() || "",
                company: formData.get("company")?.toString().trim() || "",
                interest: formData.get("interest")?.toString().trim() || "",
                teamSize: formData.get("teamSize")?.toString().trim() || "",
                context: formData.get("context")?.toString().trim() || "",
                submittedAt: new Date().toISOString()
            };

            const stored = JSON.parse(localStorage.getItem("assessment-submissions") || "[]");
            stored.push(submission);
            localStorage.setItem("assessment-submissions", JSON.stringify(stored));

            const endpoint = form.dataset.endpoint;
            let backendOk = false;

            if (endpoint) {
                backendOk = await fetch(endpoint, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(submission)
                })
                    .then((response) => response.ok)
                    .catch(() => false);
            }

            document.querySelectorAll("[data-summary]").forEach((element) => {
                const key = element.dataset.summary;
                element.textContent = submission[key] || "-";
            });

            let mailto = null;
            if (!backendOk && emailLink) {
                const lang = getCurrentLanguage();
                const dictionary = translations[lang] || translations.en;
                const subject = dictionary["index.modal.emailSubject"] || "Assessment request";
                const intro = dictionary["index.modal.emailBodyIntro"] || "Request details:";
                const bodyLines = [
                    intro,
                    "",
                    `${dictionary["index.modal.nameLabel"] || "Name:"} ${submission.fullName}`,
                    `${dictionary["index.modal.emailLabel"] || "Email:"} ${submission.email}`,
                    `${dictionary["index.modal.roleLabel"] || "Role:"} ${submission.role}`,
                    `${dictionary["index.modal.contextLabel"] || "Context:"} ${submission.context}`,
                    "",
                    `Submitted at: ${submission.submittedAt}`
                ];
                mailto = `mailto:edaza@aif369.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(bodyLines.join("\n"))}`;
                emailLink.setAttribute("href", mailto);
            }

            const successMessage = form.querySelector(".form-success");
            if (successMessage) {
                successMessage.hidden = false;
            }

            if (modal) {
                openModal();
            } else if (!backendOk && mailto) {
                window.location.href = mailto;
            }
        });
    });

    setLanguage(getInitialLanguage());
});
