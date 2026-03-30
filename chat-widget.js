/**
 * ════════════════════════════════════════════════════════════
 * AIF369 Chat Widget — Powered by Gemini 2.5
 * ────────────────────────────────────────────────────────────
 * Widget de chat flotante que aparece en la esquina inferior
 * derecha de todas las páginas. Permite al visitante hacer
 * preguntas sobre servicios, precios, metodología, etc.
 * 
 * Funcionalidad:
 * - Botón flotante (FAB) para abrir/cerrar el chat
 * - Botones rápidos predefinidos (Servicios, Precios, etc.)
 * - Historial de conversación por sesión
 * - Persistencia en BigQuery (backend guarda cada intercambio)
 * - session_id único por sesión de navegador
 * 
 * Backend: /api/chat en Cloud Run (Gemini 2.5 + fallback Ollama)
 * Drop: <script src="chat-widget.js"></script> antes de </body>
 * ════════════════════════════════════════════════════════════
 */
(function () {
    'use strict';

    // ===== Config =====
    const PROD_URL = 'https://aif369-backend-api-830685315001.us-central1.run.app';
    const DEV_URL = 'https://aif369-backend-api-dev-830685315001.us-central1.run.app';
    const isProd = location.hostname === 'aif369.com' || location.hostname === 'www.aif369.com';
    const BASE = isProd ? PROD_URL : DEV_URL;
    const CALENDLY_URL = 'https://calendly.com/edaza-aif369/30min';

    let history = [];
    let isOpen = false;
    let turnNumber = 0;
    let backendDown = false; // Track if backend is unreachable

    // Generar session_id único por sesión de navegador
    const sessionId = 'chat-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);

    // ===== Client-side Knowledge Base (fallback when backend is down) =====
    // Bilingual: ES + EN keyword matching
    const KB = [
        {
            keywords: /servicio|service|qué hacen|what do you do|qué ofrec/i,
            es: '**Nuestros servicios principales:**\n\n• **CAIO Advisory as a Service** — Acompañamiento ejecutivo: estrategia, gobierno, riesgos y adopción de IA.\n• **AI Governance & Responsible AI** — Marco de gobierno, accountability, políticas y controles.\n• **AI Risk, Privacy & Compliance** — Evaluación de riesgos, privacidad y preparación regulatoria.\n• **AI Factory Design** — Diseño de capacidades internas para construir, operar y escalar IA.\n• **Executive Workshops** — Talleres para directorio y C-level.\n\nPara más detalle, agenda una asesoría gratuita: https://calendly.com/edaza-aif369/30min o escríbenos por WhatsApp al +56 9 9754 7192',
            en: '**Our main services:**\n\n• **CAIO Advisory as a Service** — Executive advisory: strategy, governance, risk and AI adoption.\n• **AI Governance & Responsible AI** — Governance framework, accountability, policies and controls.\n• **AI Risk, Privacy & Compliance** — Risk assessment, privacy and regulatory readiness.\n• **AI Factory Design** — Internal capabilities to build, operate and scale AI.\n• **Executive Workshops** — Board and C-level enablement.\n\nFor details, book a free consultation: https://calendly.com/edaza-aif369/30min or WhatsApp +56 9 9754 7192'
        },
        {
            keywords: /precio|price|cost|cuánto cuesta|cuanto cuesta|how much|valor|tarifa|rate/i,
            es: '**🔥 BLACK WEEK — Precios especiales:**\n\nTodos nuestros cursos tienen un precio regular de USD $3,000. Durante la **Black Week**, cada curso está a solo **USD $500** — un 83% de descuento.\n\n• **IA Fundamentos** — USD $500\n• **Big Data + IA** — USD $500\n• **Automatización con Airflow** — USD $500\n• **Airflow + IA Avanzada** — USD $500\n\nOferta por tiempo limitado. Compra directo en la página del curso o por WhatsApp: +56 9 9754 7192\n\n👉 https://aif369.com/education.html',
            en: '**🔥 BLACK WEEK — Special pricing:**\n\nAll our courses have a regular price of USD $3,000. During **Black Week**, each course is just **USD $500** — 83% off.\n\n• **AI Fundamentals** — USD $500\n• **Big Data + AI** — USD $500\n• **Automation with Airflow** — USD $500\n• **Airflow + AI Advanced** — USD $500\n\nLimited time offer. Buy directly on the course page or via WhatsApp: +56 9 9754 7192\n\n👉 https://aif369.com/education.html'
        },
        {
            keywords: /scorecard|readiness|madurez|maturity|evaluaci[oó]n|assessment/i,
            es: 'El **AI Readiness Scorecard** es nuestra herramienta gratuita de evaluación de madurez en IA. En solo 5 minutos obtienes un diagnóstico de tus capacidades actuales.\n\n👉 Hazlo ahora: https://aif369.com/scorecard.html',
            en: 'The **AI Readiness Scorecard** is our free AI maturity assessment tool. In just 5 minutes you get a diagnosis of your current capabilities.\n\n👉 Take it now: https://aif369.com/scorecard.html'
        },
        {
            keywords: /método|method|369|metodolog[ií]a/i,
            es: 'El **Método 369** es nuestra metodología propietaria:\n\n• **3 Capas** de Dirección: Estratégica, Riesgo y Cumplimiento, Implementación.\n• **6 Fases** de Transformación: Descubrir, Diagnosticar, Diseñar, Desplegar, Dominar, Escalar.\n• **9 Métricas** de Control CAIO: Estrategia IA, Gobierno IA, Gestión de Riesgos, Privacidad, AI Factory Design, Observabilidad, Ética, Regulación, Formación.\n\nMás info: https://calendly.com/edaza-aif369/30min',
            en: 'The **369 Method** is our proprietary methodology:\n\n• **3 Layers** of Direction: Strategic, Risk & Compliance, Implementation.\n• **6 Phases** of Transformation: Discover, Diagnose, Design, Deploy, Master, Scale.\n• **9 CAIO Control Metrics**: AI Strategy, AI Governance, Risk Management, Privacy, AI Factory Design, Observability, Ethics, Regulation, Training.\n\nMore info: https://calendly.com/edaza-aif369/30min'
        },
        {
            keywords: /curso|course|aprender|learn|educaci[oó]n|education|capacitaci[oó]n|training|formaci[oó]n|big data|airflow|automatizaci[oó]n/i,
            es: '**🔥 BLACK WEEK — 83% OFF en todos los cursos:**\n\n• **IA Fundamentos** — Desde cero hasta aplicaciones prácticas.\n• **Big Data + IA** — Procesamiento masivo y modelos.\n• **Automatización con Airflow** — Pipelines de datos orquestados.\n• **Airflow + IA Avanzada** — ML en producción con orquestación.\n\n~~USD $3,000~~ → **USD $500** cada uno. Oferta limitada Black Week.\n\nTambién ofrecemos **Coaching Experto** personalizado y conexión con empleo en BeJoby.com.\n\n👉 Ver catálogo: https://aif369.com/education.html',
            en: '**🔥 BLACK WEEK — 83% OFF on all courses:**\n\n• **AI Fundamentals** — From zero to practical applications.\n• **Big Data + AI** — Massive processing and models.\n• **Automation with Airflow** — Orchestrated data pipelines.\n• **Airflow + AI Advanced** — ML in production with orchestration.\n\n~~USD $3,000~~ → **USD $500** each. Limited Black Week offer.\n\nWe also offer personalized **Expert Coaching** and job connections via BeJoby.com.\n\n👉 View catalog: https://aif369.com/education.html'
        },
        {
            keywords: /agendar|agenda|book|schedule|reuni[oó]n|meeting|llamada|call|cita|appointment|consulta|consult/i,
            es: '¡Perfecto! Puedes agendar una **asesoría gratuita de 30 minutos** directamente aquí:\n\n📅 https://calendly.com/edaza-aif369/30min\n\nO escríbenos por WhatsApp: +56 9 9754 7192',
            en: 'Great! You can book a **free 30-minute consultation** directly here:\n\n📅 https://calendly.com/edaza-aif369/30min\n\nOr reach us on WhatsApp: +56 9 9754 7192'
        },
        {
            keywords: /contacto|contact|whatsapp|email|correo|teléfono|phone|escribir|reach/i,
            es: '**Canales de contacto:**\n\n• 📅 Agendar asesoría: https://calendly.com/edaza-aif369/30min\n• 💬 WhatsApp: +56 9 9754 7192\n• ✉️ Email: edaza@aif369.com\n• 🌐 Web: aif369.com',
            en: '**Contact channels:**\n\n• 📅 Book consultation: https://calendly.com/edaza-aif369/30min\n• 💬 WhatsApp: +56 9 9754 7192\n• ✉️ Email: edaza@aif369.com\n• 🌐 Web: aif369.com'
        },
        {
            keywords: /erwin|fundador|founder|quién|who|about|sobre/i,
            es: 'AIF369 fue fundada por **Erwin Daza Castillo** — CAIO Advisor, Data & AI Architect, AI Governance Strategist. Creador del Método 369 para adopción gobernada de IA. Empresa chilena que emite boleta de honorarios.\n\nConócelo: https://calendly.com/edaza-aif369/30min',
            en: 'AIF369 was founded by **Erwin Daza Castillo** — CAIO Advisor, Data & AI Architect, AI Governance Strategist. Creator of the 369 Method for governed AI adoption. Chilean company.\n\nMeet him: https://calendly.com/edaza-aif369/30min'
        },
        {
            keywords: /bejoby|empleo|job|trabajo|employment|hiring|contrat/i,
            es: '**BeJoby.com** es nuestra plataforma de empleo en IA y datos. Si completaste cursos en AIF369, puedes publicar tu perfil y conectar con empresas que buscan talento.\n\n👉 https://bejoby.com\n\nTambién puedes hablar con nosotros: +56 9 9754 7192',
            en: '**BeJoby.com** is our AI & data job platform. If you completed AIF369 courses, you can publish your profile and connect with companies looking for talent.\n\n👉 https://bejoby.com\n\nYou can also reach us: +56 9 9754 7192'
        },
        {
            keywords: /coaching|mentor|guía|guide|acompañamiento/i,
            es: 'Ofrecemos **Coaching Experto** en 3 planes:\n\n• **Básico** — 2 sesiones de coaching + revisión de CV.\n• **Profesional** — 4 sesiones + portfolio + simulación de entrevistas.\n• **Premium** — 8 sesiones + acceso prioritario a ofertas en BeJoby.com.\n\n👉 Más info: https://aif369.com/coaching-data.html',
            en: 'We offer **Expert Coaching** in 3 plans:\n\n• **Basic** — 2 coaching sessions + CV review.\n• **Professional** — 4 sessions + portfolio + interview simulation.\n• **Premium** — 8 sessions + priority access to BeJoby.com listings.\n\n👉 More info: https://aif369.com/coaching-data.html'
        },
        {
            keywords: /regulaci[oó]n|regulation|ley|law|compliance|normativa|eu ai act|ley 21|bolet[ií]n/i,
            es: 'AIF369 te ayuda con el contexto regulatorio:\n\n• **EU AI Act** — Marco de referencia para clasificación de riesgo de sistemas IA.\n• **Chile Ley 21.719** — Protección de datos personales (vigencia 1 dic 2026).\n• **Boletín 16821-19** — Proyecto de ley de IA en Chile, en tramitación.\n\nConsulta con nuestro experto: https://calendly.com/edaza-aif369/30min',
            en: 'AIF369 helps with the regulatory landscape:\n\n• **EU AI Act** — Risk classification framework for AI systems.\n• **Chile Law 21.719** — Personal data protection (effective Dec 1, 2026).\n• **Bill 16821-19** — AI law project in Chile, under review.\n\nConsult our expert: https://calendly.com/edaza-aif369/30min'
        },
        {
            keywords: /hola|hello|hi|hey|buenos|buenas|good morning|good afternoon/i,
            es: '¡Hola! Soy el asistente de AIF369. Puedo ayudarte con información sobre:\n\n• Nuestros **servicios** de IA y gobernanza\n• **Cursos** y capacitación\n• **Coaching** experto\n• **Empleo** en BeJoby.com\n• **Agendar** una asesoría gratuita\n\n¿En qué te puedo ayudar?',
            en: 'Hello! I\'m the AIF369 assistant. I can help you with:\n\n• Our **AI governance services**\n• **Courses** and training\n• Expert **coaching**\n• **Jobs** on BeJoby.com\n• **Book** a free consultation\n\nHow can I help you?'
        }
    ];

    /** Detect if message is English */
    function isEnglish(text) {
        const enWords = /\b(the|is|are|what|how|can|do|does|your|you|we|our|about|services?|price|cost|book|schedule|hello|hi|hey|please|thanks|thank|information|help)\b/i;
        return enWords.test(text);
    }

    /** Find best KB match for a user message */
    function kbLookup(text) {
        const lang = isEnglish(text) ? 'en' : 'es';
        for (const entry of KB) {
            if (entry.keywords.test(text)) {
                return entry[lang];
            }
        }
        // No match — generic fallback
        if (lang === 'en') {
            return "I don't have that specific information right now. For personalized help, reach us on WhatsApp: +56 9 9754 7192 or book a free consultation: https://calendly.com/edaza-aif369/30min";
        }
        return 'No tengo esa información específica en este momento. Para consultas personalizadas, escríbenos por WhatsApp: +56 9 9754 7192 o agenda una asesoría gratuita: https://calendly.com/edaza-aif369/30min';
    }

    // ===== Inject CSS =====
    const style = document.createElement('style');
    style.textContent = `
        #aif-chat-fab {
            position: fixed; bottom: 24px; right: 24px; z-index: 9999;
            width: 60px; height: 60px; border-radius: 50%;
            background: linear-gradient(135deg, #0088FF, #00D9CC);
            border: none; cursor: pointer; box-shadow: 0 4px 20px rgba(0,136,255,0.4);
            display: flex; align-items: center; justify-content: center;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        #aif-chat-fab:hover { transform: scale(1.08); box-shadow: 0 6px 28px rgba(0,136,255,0.5); }
        #aif-chat-fab svg { width: 28px; height: 28px; fill: white; }
        #aif-chat-fab .close-icon { display: none; }
        #aif-chat-fab.open .chat-icon { display: none; }
        #aif-chat-fab.open .close-icon { display: block; }

        #aif-chat-panel {
            position: fixed; bottom: 96px; right: 24px; z-index: 9998;
            width: 380px; max-width: calc(100vw - 32px); height: 520px; max-height: calc(100vh - 140px);
            background: #0A1628; border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px; display: flex; flex-direction: column;
            box-shadow: 0 16px 64px rgba(0,0,0,0.6); overflow: hidden;
            transform: translateY(20px) scale(0.95); opacity: 0; pointer-events: none;
            transition: transform 0.25s cubic-bezier(0.4,0,0.2,1), opacity 0.25s ease;
        }
        #aif-chat-panel.open {
            transform: translateY(0) scale(1); opacity: 1; pointer-events: auto;
        }

        .aif-chat-header {
            padding: 16px 20px; background: #0F1F35;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            display: flex; align-items: center; gap: 12px;
        }
        .aif-chat-header .avatar {
            width: 36px; height: 36px; border-radius: 50%;
            background: linear-gradient(135deg, #0088FF, #00D9CC);
            display: flex; align-items: center; justify-content: center;
            font-weight: 700; font-size: 14px; color: white; flex-shrink: 0;
        }
        .aif-chat-header .info h4 { color: #fff; font-size: 14px; margin: 0; font-weight: 600; }
        .aif-chat-header .info p { color: #A8B8D8; font-size: 12px; margin: 2px 0 0; }

        .aif-chat-messages {
            flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px;
            scrollbar-width: thin; scrollbar-color: rgba(255,255,255,0.1) transparent;
        }
        .aif-chat-messages::-webkit-scrollbar { width: 4px; }
        .aif-chat-messages::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }

        .aif-msg {
            max-width: 85%; padding: 10px 14px; border-radius: 12px;
            font-size: 14px; line-height: 1.5; word-wrap: break-word;
            font-family: 'Inter', -apple-system, sans-serif;
        }
        .aif-msg.bot {
            background: #162B45; color: #E2E8F0; align-self: flex-start;
            border-bottom-left-radius: 4px;
        }
        .aif-msg.user {
            background: #0088FF; color: white; align-self: flex-end;
            border-bottom-right-radius: 4px;
        }
        .aif-msg.typing {
            background: #162B45; color: #7B8BA8; align-self: flex-start;
            border-bottom-left-radius: 4px;
        }
        .aif-msg.typing .dots span {
            display: inline-block; width: 6px; height: 6px; border-radius: 50%;
            background: #7B8BA8; margin: 0 2px; animation: aifBounce 1.4s infinite ease-in-out;
        }
        .aif-msg.typing .dots span:nth-child(2) { animation-delay: 0.2s; }
        .aif-msg.typing .dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes aifBounce {
            0%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-6px); }
        }

        .aif-chat-input {
            padding: 12px 16px; border-top: 1px solid rgba(255,255,255,0.08);
            display: flex; gap: 8px; background: #0F1F35;
        }
        .aif-chat-input input {
            flex: 1; background: #162B45; border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px; padding: 10px 14px; color: #fff; font-size: 14px;
            font-family: 'Inter', -apple-system, sans-serif; outline: none;
        }
        .aif-chat-input input::placeholder { color: #7B8BA8; }
        .aif-chat-input input:focus { border-color: #0088FF; }
        .aif-chat-input button {
            background: #0088FF; border: none; border-radius: 8px;
            padding: 10px 14px; cursor: pointer; display: flex; align-items: center;
            transition: background 0.2s;
        }
        .aif-chat-input button:hover { background: #3AA0FF; }
        .aif-chat-input button:disabled { opacity: 0.5; cursor: not-allowed; }
        .aif-chat-input button svg { width: 18px; height: 18px; fill: white; }

        .aif-quick-actions {
            display: flex; flex-wrap: wrap; gap: 6px; padding: 0 16px 12px;
        }
        .aif-quick-btn {
            background: rgba(0,136,255,0.1); border: 1px solid rgba(0,136,255,0.3);
            border-radius: 20px; padding: 6px 12px; color: #3AA0FF; font-size: 12px;
            cursor: pointer; font-family: 'Inter', -apple-system, sans-serif;
            transition: all 0.2s;
        }
        .aif-quick-btn:hover { background: rgba(0,136,255,0.2); border-color: #0088FF; }

        .aif-msg a {
            color: #3AA0FF; text-decoration: underline;
            word-break: break-all;
        }
        .aif-msg a:hover { color: #66B8FF; }
        .aif-msg .wsp-link {
            display: inline-flex; align-items: center; gap: 4px;
            background: rgba(37,211,102,0.12); border: 1px solid rgba(37,211,102,0.3);
            border-radius: 6px; padding: 2px 8px; margin: 2px 0;
            color: #25D366; text-decoration: none; font-weight: 500;
            transition: background 0.2s;
        }
        .aif-msg .wsp-link:hover { background: rgba(37,211,102,0.22); color: #25D366; }
        .aif-msg .wsp-link svg { width: 14px; height: 14px; flex-shrink: 0; }

        .aif-msg .cal-cta {
            display: flex; align-items: center; gap: 8px;
            background: linear-gradient(135deg, rgba(0,136,255,0.15), rgba(0,217,204,0.15));
            border: 1px solid rgba(0,136,255,0.35);
            border-radius: 10px; padding: 10px 14px; margin-top: 8px;
            color: #fff; text-decoration: none; font-size: 13px; font-weight: 500;
            cursor: pointer; transition: all 0.2s;
        }
        .aif-msg .cal-cta:hover {
            background: linear-gradient(135deg, rgba(0,136,255,0.25), rgba(0,217,204,0.25));
            border-color: #0088FF; transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,136,255,0.3);
        }
        .aif-msg .cal-cta svg { width: 18px; height: 18px; flex-shrink: 0; }
        .aif-msg .cal-cta .cal-label { flex: 1; }
        .aif-msg .cal-cta .cal-arrow { font-size: 16px; opacity: 0.6; }

        @media (max-width: 480px) {
            #aif-chat-panel { right: 8px; bottom: 80px; width: calc(100vw - 16px); height: calc(100vh - 100px); }
            #aif-chat-fab { bottom: 16px; right: 16px; width: 52px; height: 52px; }
        }
    `;
    document.head.appendChild(style);

    // ===== Detect browser language =====
    const browserLang = (navigator.language || navigator.userLanguage || 'es').toLowerCase();
    const isEN = browserLang.startsWith('en');

    // ===== Inject HTML =====
    const fab = document.createElement('button');
    fab.id = 'aif-chat-fab';
    fab.setAttribute('aria-label', 'Abrir chat');
    fab.innerHTML = `
        <svg class="chat-icon" viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/><path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>
        <svg class="close-icon" viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
    `;

    const panel = document.createElement('div');
    panel.id = 'aif-chat-panel';
    panel.innerHTML = `
        <div class="aif-chat-header">
            <div class="avatar">AI</div>
            <div class="info">
                <h4>AIF369 Assistant</h4>
                <p>IA, Datos y Cloud ・ Responde al instante</p>
            </div>
        </div>
        <div class="aif-chat-messages" id="aif-messages"></div>
        <div class="aif-quick-actions" id="aif-quick-actions">
            <button class="aif-quick-btn" data-msg="${isEN ? 'What services do you offer?' : '¿Qué servicios ofrecen?'}">${isEN ? 'Services' : 'Servicios'}</button>
            <button class="aif-quick-btn" data-msg="${isEN ? 'What are your course options?' : '¿Qué cursos tienen?'}">${isEN ? 'Courses' : 'Cursos'}</button>
            <button class="aif-quick-btn" data-msg="${isEN ? 'How much does it cost?' : '¿Cuánto cuesta un diagnóstico?'}">${isEN ? 'Pricing' : 'Precios'}</button>
            <button class="aif-quick-btn" data-msg="${isEN ? 'What is the AI Readiness Scorecard?' : '¿Qué es el AI Readiness Scorecard?'}">Scorecard</button>
            <button class="aif-quick-btn" data-action="calendly">📅 ${isEN ? 'Book' : 'Agendar'}</button>
        </div>
        <div class="aif-chat-input">
            <input type="text" id="aif-input" placeholder="${isEN ? 'Ask your question...' : 'Escribe tu pregunta...'}" autocomplete="off">
            <button id="aif-send" aria-label="Enviar">
                <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            </button>
        </div>
    `;

    document.body.appendChild(panel);
    document.body.appendChild(fab);

    // ===== Logic =====
    const messages = document.getElementById('aif-messages');
    const input = document.getElementById('aif-input');
    const sendBtn = document.getElementById('aif-send');
    const quickActions = document.getElementById('aif-quick-actions');

    // Welcome message
    addMessage('bot', isEN
        ? 'Hello! I\'m the AIF369 assistant. How can I help you today? I can tell you about our services, courses, pricing, or help you find the right solution for your organization.'
        : '¡Hola! Soy el asistente de AIF369. ¿En qué puedo ayudarte hoy? Puedo contarte sobre nuestros servicios, cursos, precios, o ayudarte a encontrar la solución ideal para tu organización.');

    fab.addEventListener('click', toggleChat);

    function toggleChat() {
        isOpen = !isOpen;
        fab.classList.toggle('open', isOpen);
        panel.classList.toggle('open', isOpen);
        if (isOpen) input.focus();
    }

    const WSP_ICON = '<svg viewBox="0 0 24 24" fill="#25D366"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>';

    function formatBotText(text) {
        // 1) Bold & newlines
        let out = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');

        // 2) URLs → clickable links (strip trailing . , ; : ! ? ) ])
        out = out.replace(
            /(https?:\/\/[^\s<>"']+?)([.,;:!?)\]]*(?=\s|<br>|$))/gi,
            '<a href="$1" target="_blank" rel="noopener">$1</a>$2'
        );

        // 3) Chilean phone numbers → WhatsApp link
        //    Matches: +56 9 9754 7192, +56997547192, +56 9 97547192, etc.
        out = out.replace(
            /\+56[\s.-]?9[\s.-]?(\d{4})[\s.-]?(\d{4})/g,
            function(match, p1, p2) {
                const clean = '56' + '9' + p1 + p2;
                return '<a class="wsp-link" href="https://wa.me/' + clean + '" target="_blank" rel="noopener">' + WSP_ICON + ' +56 9 ' + p1 + ' ' + p2 + '</a>';
            }
        );

        // 4) Generic international phone with WhatsApp hint
        //    If text says "WhatsApp" near a +XX number not already linked
        out = out.replace(
            /(?:WhatsApp|whatsapp|Whatsapp|wsp|WSP)[^<]{0,30}\+(\d{1,3})[\s.-]?(\d[\s\d.-]{6,12}\d)(?![^<]*<\/a>)/gi,
            function(match, cc, num) {
                const clean = cc + num.replace(/[\s.-]/g, '');
                if (match.includes('wsp-link')) return match; // already linked
                return match.replace(
                    '+' + cc + num.match(/[\s.-]?/)[0] + num,
                    '<a class="wsp-link" href="https://wa.me/' + clean + '" target="_blank" rel="noopener">' + WSP_ICON + ' +' + cc + ' ' + num.trim() + '</a>'
                );
            }
        );

        return out;
    }

    function addMessage(role, text) {
        const div = document.createElement('div');
        div.className = `aif-msg ${role}`;
        div.innerHTML = (role === 'bot') ? formatBotText(text) : escapeHtml(text);
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
        return div;
    }

    function escapeHtml(str) {
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    function showTyping() {
        const div = document.createElement('div');
        div.className = 'aif-msg typing';
        div.id = 'aif-typing';
        div.innerHTML = '<div class="dots"><span></span><span></span><span></span></div>';
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    function hideTyping() {
        const el = document.getElementById('aif-typing');
        if (el) el.remove();
    }

    function openCalendly() {
        if (window.Calendly) {
            window.Calendly.initPopupWidget({ url: CALENDLY_URL });
        } else {
            window.open(CALENDLY_URL, '_blank');
        }
    }

    function appendCalendlyCTA(parentDiv) {
        const cta = document.createElement('a');
        cta.className = 'cal-cta';
        cta.href = CALENDLY_URL;
        cta.target = '_blank';
        cta.rel = 'noopener';
        cta.addEventListener('click', function(e) {
            e.preventDefault();
            openCalendly();
        });
        cta.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg><span class="cal-label">Agendar asesoría gratuita de 30 min</span><span class="cal-arrow">→</span>';
        parentDiv.appendChild(cta);
    }

    // Detect scheduling-related keywords in bot reply
    const SCHEDULE_KEYWORDS = /agenda|agendar|coordin|reuni[oó]n|conversa|llamada|cita|contactar|cotizaci[oó]n|whatsapp|diagnóstico/i;

    async function sendMessage(text) {
        if (!text.trim()) return;

        // Hide quick actions after first message
        quickActions.style.display = 'none';

        addMessage('user', text);
        history.push({ role: 'user', content: text });
        turnNumber++;

        input.value = '';
        sendBtn.disabled = true;
        showTyping();

        let reply = null;
        let usedFallback = false;

        // --- Try backend first (skip if we already know it's down to save time) ---
        if (!backendDown) {
            try {
                const controller = new AbortController();
                const timeout = setTimeout(() => controller.abort(), 8000); // 8s timeout

                const res = await fetch(`${BASE}/api/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: text,
                        history: history,
                        session_id: sessionId,
                        turn_number: turnNumber,
                        source_page: window.location.pathname
                    }),
                    signal: controller.signal
                });
                clearTimeout(timeout);
                const data = await res.json();
                reply = data.response;
            } catch (e) {
                console.warn('AIF369 Chat: backend unreachable, using local KB fallback.', e.message);
                backendDown = true;
                // Retry backend after 2 minutes
                setTimeout(() => { backendDown = false; }, 120000);
            }
        }

        // --- Fallback: client-side knowledge base ---
        if (!reply) {
            reply = kbLookup(text);
            usedFallback = true;
        }

        hideTyping();
        const msgDiv = addMessage('bot', reply);
        history.push({ role: 'assistant', content: reply });

        // If reply mentions scheduling/contact, append Calendly CTA
        if (SCHEDULE_KEYWORDS.test(reply) || SCHEDULE_KEYWORDS.test(text)) {
            appendCalendlyCTA(msgDiv);
        }

        sendBtn.disabled = false;
        input.focus();
    }

    sendBtn.addEventListener('click', () => sendMessage(input.value));
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(input.value);
        }
    });

    // Quick action buttons
    quickActions.addEventListener('click', (e) => {
        const btn = e.target.closest('.aif-quick-btn');
        if (!btn) return;
        if (btn.dataset.action === 'calendly') {
            quickActions.style.display = 'none';
            addMessage('user', 'Quiero agendar una asesoría');
            const msgDiv = addMessage('bot', '¡Excelente! Puedes elegir el día y hora que más te acomode directamente en nuestro calendario:');
            appendCalendlyCTA(msgDiv);
            return;
        }
        sendMessage(btn.dataset.msg);
    });
})();
