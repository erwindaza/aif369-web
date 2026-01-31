document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.querySelector(".nav-toggle");
    const links = document.querySelector(".nav-links");

    if (toggle && links) {
        toggle.addEventListener("click", function () {
            links.classList.toggle("open");
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
            "index.cta.includes": "Qué incluye",
            "index.cta.item1": "Radiografía rápida de capacidades actuales.",
            "index.cta.item2": "Mapa de oportunidades de alto impacto.",
            "index.cta.item3": "Riesgos clave de datos y gobernanza a revisar.",
            "index.cta.item4": "Propuesta de siguiente paso clara y accionable.",
            "index.cta.note": "Esta sesión no es comercial tradicional - el objetivo es claridad técnica y estratégica.",
            "index.modal.title": "Resumen de solicitud enviada",
            "index.modal.subtitle": "Estos son los datos enviados. Guarda este resumen y revisa dónde se almacenan.",
            "index.modal.nameLabel": "Nombre:",
            "index.modal.emailLabel": "Email:",
            "index.modal.roleLabel": "Cargo:",
            "index.modal.contextLabel": "Contexto:",
            "index.modal.storageNote": "Por ahora los datos quedan guardados localmente en el navegador (storage embebido). Más adelante podemos conectarlo a una base de datos real.",
            "index.modal.emailNote": "Al enviar se abrirá tu cliente de correo para mandar la solicitud a erwin.daza@gmail.com.",
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
            "services.card2.title": "Implementación de casos de uso",
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
            "education.card2.link": "Ver curso",
            "education.card3.title": "Material para CAIO y comités",
            "education.card3.text": "Plantillas, matrices y esquemas para documentar decisiones de IA y gestionar riesgo sin apagar la innovación.",
            "education.card3.link": "Solicitar material",
            "education.footer.text": "IA, datos y cloud para la empresa moderna.",
            "blog.title": "Blog AIF369 - IA, Datos y Cloud",
            "blog.description": "Blog de AIF369 con análisis y contenidos de vanguardia sobre inteligencia artificial, datos y cloud para ejecutivos y equipos técnicos.",
            "blog.header.title": "Blog AIF369",
            "blog.header.subtitle": "Ideas, aprendizajes y marcos de trabajo para quienes lideran iniciativas de IA, datos y cloud.",
            "blog.post1.tag": "Estrategia de IA",
            "blog.post1.title": "2026: cuando la IA deja de asistir y empieza a decidir",
            "blog.post1.meta": "Lectura de 10 minutos - Nivel: Ejecutivo",
            "blog.post1.text": "Qué ocurre cuando los agentes y modelos empiezan a tomar decisiones operativas sin que cada paso pase por una persona, y qué significa esto para el CAIO, el CIO y los equipos de riesgo.",
            "blog.post1.link": "Leer artículo completo",
            "blog.post2.tag": "Arquitectura de datos",
            "blog.post2.title": "De data lake a plataforma de decisiones - una ruta práctica",
            "blog.post2.meta": "Lectura de 8 minutos - Nivel: Arquitectura",
            "blog.post2.text": "Cinco decisiones arquitectónicas que separan un repositorio de datos de una verdadera plataforma que habilita analítica, IA y gobierno.",
            "blog.post2.link": "Ver ejemplo de estructura",
            "blog.aside.title": "Para quién escribimos",
            "blog.aside.text": "CAIO, CIO, CDO, CTO, líderes de datos, arquitectura, transformación digital y equipos de innovación que necesitan bajar IA a la realidad.",
            "blog.aside2.title": "Recibir próximos artículos",
            "blog.aside2.text": "Pronto habilitaremos una suscripción simple para recibir los próximos análisis en su correo corporativo.",
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
            "product.pricing.title": "Precio y tiempos",
            "product.pricing.subtitle": "Diseñado para empresas medianas y corporaciones que necesitan claridad rápida.",
            "product.pricing.card1.title": "Starter",
            "product.pricing.card1.price": "USD 1.500",
            "product.pricing.card1.text": "Ideal para equipos con un piloto activo.",
            "product.pricing.card1.item1": "Entrega en 10 días hábiles.",
            "product.pricing.card1.item2": "1 sesión ejecutiva.",
            "product.pricing.card1.item3": "Plantillas y roadmap incluidos.",
            "product.pricing.card2.title": "Enterprise",
            "product.pricing.card2.price": "USD 3.000",
            "product.pricing.card2.text": "Para organizaciones con múltiples áreas.",
            "product.pricing.card2.item1": "Entrega en 15 días hábiles.",
            "product.pricing.card2.item2": "2 sesiones ejecutivas.",
            "product.pricing.card2.item3": "Diagnóstico extendido por unidad.",
            "product.cta.title": "Solicitar el kit",
            "product.cta.subtitle": "Escríbenos para recibir el detalle completo y coordinar fechas.",
            "product.cta.button": "Quiero el AI Governance Starter Kit",
            "product.footer.text": "Producto digital de AIF369 para acelerar gobierno de IA.",
            "post.title": "Título del artículo - Blog AIF369",
            "post.description": "Plantilla base para artículos del blog de AIF369 sobre IA, datos y cloud.",
            "post.tag": "Categoría",
            "post.header": "Título del artículo",
            "post.meta": "Lectura de X minutos - Nivel: Ejecutivo o Técnico.",
            "post.intro": "Introduce el problema o contexto de negocio. Explica por qué el lector debería importar su atención en este tema.",
            "post.section1": "Subtítulo 1",
            "post.section1.text": "Desarrollo de la idea principal con ejemplos. Mantén los párrafos cortos y claros.",
            "post.section2": "Subtítulo 2",
            "post.section2.item1": "Punto clave uno.",
            "post.section2.item2": "Punto clave dos.",
            "post.section2.item3": "Punto clave tres.",
            "post.section3": "Qué hacer después de leer esto",
            "post.section3.text": "Termina siempre con un llamado a la acción claro, orientado a que el lector tome una decisión o evalúe algo dentro de su organización.",
            "post.back": "Volver al blog",
            "post.footer.text": "IA, datos y cloud para la empresa moderna.",
            "article.title": "2026: cuando la IA deja de asistir y empieza a decidir - Blog AIF369",
            "article.description": "Análisis sobre el momento en que la IA empieza a tomar decisiones operativas y los cambios de gobierno, riesgo y arquitectura que esto exige.",
            "article.tag": "Estrategia de IA",
            "article.header": "2026: cuando la IA deja de asistir y empieza a decidir",
            "article.meta": "Lectura de 10 minutos - Pensado para CAIO, CIO, CDO y equipos de arquitectura.",
            "article.intro": "Durante años hablamos de inteligencia artificial como un asistente que sugiere, recomienda o responde. El cambio real empieza cuando los modelos y agentes dejan de ser solo asistentes y toman decisiones concretas sobre clientes, procesos y recursos.",
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
            "article.section4.text": "La empresa que llegue sólida a este escenario no será la que más modelos tenga en producción, sino la que haya logrado alinear arquitectura, datos y gobierno en un mismo lenguaje y modelo operativo.",
            "article.cta": "En AIF369 ayudamos a definir esa línea entre asistencia y decisión, y a construir las arquitecturas, procesos y comités que permiten avanzar sin frenar la innovación.",
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
            "index.cta.includes": "What’s included",
            "index.cta.item1": "Rapid snapshot of current capabilities.",
            "index.cta.item2": "Map of high-impact opportunities.",
            "index.cta.item3": "Key data and governance risks to review.",
            "index.cta.item4": "Clear, actionable next-step proposal.",
            "index.cta.note": "This session isn’t a traditional sales call - the goal is technical and strategic clarity.",
            "index.modal.title": "Submitted request summary",
            "index.modal.subtitle": "These are the details you submitted. Save this summary and review where the data is stored.",
            "index.modal.nameLabel": "Name:",
            "index.modal.emailLabel": "Email:",
            "index.modal.roleLabel": "Title:",
            "index.modal.contextLabel": "Context:",
            "index.modal.storageNote": "For now the data is saved locally in the browser (embedded storage). We can connect this to a real database later.",
            "index.modal.emailNote": "Sending will open your email client to send the request to erwin.daza@gmail.com.",
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
            "services.card2.title": "Use case implementation",
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
            "education.card2.link": "View course",
            "education.card3.title": "Materials for CAIOs and committees",
            "education.card3.text": "Templates, matrices, and frameworks to document AI decisions and manage risk without shutting down innovation.",
            "education.card3.link": "Request material",
            "education.footer.text": "AI, data, and cloud for the modern enterprise.",
            "blog.title": "AIF369 Blog - AI, Data & Cloud",
            "blog.description": "AIF369 blog with cutting-edge analysis and content on artificial intelligence, data, and cloud for executives and technical teams.",
            "blog.header.title": "AIF369 Blog",
            "blog.header.subtitle": "Ideas, lessons, and frameworks for leaders of AI, data, and cloud initiatives.",
            "blog.post1.tag": "AI strategy",
            "blog.post1.title": "2026: when AI stops assisting and starts deciding",
            "blog.post1.meta": "10-minute read - Level: Executive",
            "blog.post1.text": "What happens when agents and models begin to make operational decisions without every step going through a person, and what that means for the CAIO, CIO, and risk teams.",
            "blog.post1.link": "Read full article",
            "blog.post2.tag": "Data architecture",
            "blog.post2.title": "From data lake to decision platform - a practical path",
            "blog.post2.meta": "8-minute read - Level: Architecture",
            "blog.post2.text": "Five architectural decisions that separate a data repository from a true platform that enables analytics, AI, and governance.",
            "blog.post2.link": "View structure example",
            "blog.aside.title": "Who we write for",
            "blog.aside.text": "CAIOs, CIOs, CDOs, CTOs, data leaders, architecture, digital transformation, and innovation teams that need to bring AI down to reality.",
            "blog.aside2.title": "Get upcoming articles",
            "blog.aside2.text": "We will soon offer a simple subscription to receive upcoming analysis in your corporate inbox.",
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
            "product.pricing.title": "Pricing and timeline",
            "product.pricing.subtitle": "Designed for mid-market and enterprise teams needing fast clarity.",
            "product.pricing.card1.title": "Starter",
            "product.pricing.card1.price": "USD 1,500",
            "product.pricing.card1.text": "Ideal for teams with an active pilot.",
            "product.pricing.card1.item1": "Delivery in 10 business days.",
            "product.pricing.card1.item2": "1 executive session.",
            "product.pricing.card1.item3": "Templates and roadmap included.",
            "product.pricing.card2.title": "Enterprise",
            "product.pricing.card2.price": "USD 3,000",
            "product.pricing.card2.text": "For organizations with multiple units.",
            "product.pricing.card2.item1": "Delivery in 15 business days.",
            "product.pricing.card2.item2": "2 executive sessions.",
            "product.pricing.card2.item3": "Extended assessment per unit.",
            "product.cta.title": "Request the kit",
            "product.cta.subtitle": "Contact us to receive the full details and schedule dates.",
            "product.cta.button": "I want the AI Governance Starter Kit",
            "product.footer.text": "AIF369 digital product to accelerate AI governance.",
            "post.title": "Article title - AIF369 Blog",
            "post.description": "Base template for AIF369 blog articles on AI, data, and cloud.",
            "post.tag": "Category",
            "post.header": "Article title",
            "post.meta": "X-minute read - Level: Executive or Technical.",
            "post.intro": "Introduce the business problem or context. Explain why the reader should pay attention to this topic.",
            "post.section1": "Subtitle 1",
            "post.section1.text": "Develop the main idea with examples. Keep paragraphs short and clear.",
            "post.section2": "Subtitle 2",
            "post.section2.item1": "Key point one.",
            "post.section2.item2": "Key point two.",
            "post.section2.item3": "Key point three.",
            "post.section3": "What to do after reading this",
            "post.section3.text": "Always finish with a clear call to action, aimed at helping the reader make a decision or evaluate something within their organization.",
            "post.back": "Back to blog",
            "post.footer.text": "AI, data, and cloud for the modern enterprise.",
            "article.title": "2026: when AI stops assisting and starts deciding - AIF369 Blog",
            "article.description": "Analysis of the moment when AI starts making operational decisions and the governance, risk, and architecture changes this requires.",
            "article.tag": "AI strategy",
            "article.header": "2026: when AI stops assisting and starts deciding",
            "article.meta": "10-minute read - For CAIOs, CIOs, CDOs, and architecture teams.",
            "article.intro": "For years we talked about artificial intelligence as an assistant that suggests, recommends, or responds. The real shift begins when models and agents stop being just assistants and start making concrete decisions about customers, processes, and resources.",
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
            "article.section4.text": "The company that arrives strong in this scenario won’t be the one with the most models in production, but the one that has aligned architecture, data, and governance in a single language and operating model.",
            "article.cta": "At AIF369 we help define that line between assistance and decision, and build the architectures, processes, and committees that let you move forward without slowing innovation.",
            "article.back": "Back to blog",
            "article.footer.text": "AI, data, and cloud for the modern enterprise."
        }
    };

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
                element.textContent = dictionary[key];
            }
        });

        document.querySelectorAll("[data-i18n-content]").forEach((element) => {
            const key = element.dataset.i18nContent;
            if (dictionary[key]) {
                element.setAttribute("content", dictionary[key]);
            }
        });
    }

    function getInitialLanguage() {
        const stored = localStorage.getItem("site-lang");
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
        return localStorage.getItem("site-lang") || getInitialLanguage();
    }

    function setLanguage(lang) {
        const target = translations[lang] ? lang : "en";
        localStorage.setItem("site-lang", target);
        applyTranslations(target);
    }

    const langToggle = document.querySelector(".lang-toggle");
    if (langToggle) {
        langToggle.addEventListener("click", function () {
            const current = getCurrentLanguage();
            const next = current === "es" ? "en" : "es";
            setLanguage(next);
        });
    }

    const contactForm = document.querySelector(".contact-form");
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

    if (contactForm) {
        contactForm.addEventListener("submit", async function (event) {
            event.preventDefault();
            
            const submitButton = contactForm.querySelector('button[type="submit"]');
            const originalText = submitButton.textContent;
            submitButton.disabled = true;
            submitButton.textContent = 'Enviando...';
            
            const formData = new FormData(contactForm);
            const submission = {
                name: formData.get("fullName")?.toString().trim() || "",
                email: formData.get("email")?.toString().trim() || "",
                company: formData.get("role")?.toString().trim() || "",
                message: formData.get("context")?.toString().trim() || "",
                source_page: window.location.href
            };

            try {
                // Enviar a Cloud Run backend
                const response = await fetch('https://aif369-backend-api-830685315001.us-central1.run.app/api/contact', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(submission)
                });

                const result = await response.json();

                if (response.ok) {
                    // Guardar también en localStorage para historial local
                    const stored = JSON.parse(localStorage.getItem("assessment-submissions") || "[]");
                    stored.push({
                        ...submission,
                        submission_id: result.submission_id,
                        submittedAt: new Date().toISOString()
                    });
                    localStorage.setItem("assessment-submissions", JSON.stringify(stored));

                    // Actualizar modal con los datos
                    document.querySelectorAll("[data-summary]").forEach((element) => {
                        const key = element.dataset.summary;
                        if (key === 'fullName') element.textContent = submission.name;
                        else if (key === 'role') element.textContent = submission.company;
                        else if (key === 'context') element.textContent = submission.message;
                        else element.textContent = submission[key] || "-";
                    });

                    // Actualizar link de email
                    if (emailLink) {
                        const lang = getCurrentLanguage();
                        const dictionary = translations[lang] || translations.en;
                        const subject = dictionary["index.modal.emailSubject"] || "Assessment request";
                        const intro = dictionary["index.modal.emailBodyIntro"] || "Request details:";
                        const bodyLines = [
                            intro,
                            "",
                            `${dictionary["index.modal.nameLabel"] || "Name:"} ${submission.name}`,
                            `${dictionary["index.modal.emailLabel"] || "Email:"} ${submission.email}`,
                            `${dictionary["index.modal.roleLabel"] || "Role:"} ${submission.company}`,
                            `${dictionary["index.modal.contextLabel"] || "Context:"} ${submission.message}`,
                            "",
                            `Submission ID: ${result.submission_id}`
                        ];
                        const mailto = `mailto:erwin.daza@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(bodyLines.join("\n"))}`;
                        emailLink.setAttribute("href", mailto);
                    }

                    contactForm.reset();
                    openModal();
                } else {
                    alert('Error al enviar el formulario: ' + (result.error || 'Error desconocido'));
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error de conexión. Por favor intenta de nuevo más tarde.');
            } finally {
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            }
        });
    }

    setLanguage(getInitialLanguage());
});
