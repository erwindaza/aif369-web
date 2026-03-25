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

    let history = [];
    let isOpen = false;
    let turnNumber = 0;

    // Generar session_id único por sesión de navegador
    const sessionId = 'chat-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);

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

        @media (max-width: 480px) {
            #aif-chat-panel { right: 8px; bottom: 80px; width: calc(100vw - 16px); height: calc(100vh - 100px); }
            #aif-chat-fab { bottom: 16px; right: 16px; width: 52px; height: 52px; }
        }
    `;
    document.head.appendChild(style);

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
            <button class="aif-quick-btn" data-msg="¿Qué servicios ofrecen?">Servicios</button>
            <button class="aif-quick-btn" data-msg="¿Cuánto cuesta un diagnóstico?">Precios</button>
            <button class="aif-quick-btn" data-msg="¿Qué es el AI Readiness Scorecard?">Scorecard</button>
            <button class="aif-quick-btn" data-msg="Quiero agendar una conversación">Agendar</button>
        </div>
        <div class="aif-chat-input">
            <input type="text" id="aif-input" placeholder="Escribe tu pregunta..." autocomplete="off">
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
    addMessage('bot', '¡Hola! Soy el asistente de AIF369. ¿En qué puedo ayudarte hoy? Puedo contarte sobre nuestros servicios, precios, o ayudarte a encontrar la solución ideal para tu organización.');

    fab.addEventListener('click', toggleChat);

    function toggleChat() {
        isOpen = !isOpen;
        fab.classList.toggle('open', isOpen);
        panel.classList.toggle('open', isOpen);
        if (isOpen) input.focus();
    }

    function addMessage(role, text) {
        const div = document.createElement('div');
        div.className = `aif-msg ${role}`;
        // Simple markdown-like formatting
        div.innerHTML = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
        return div;
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

        try {
            const res = await fetch(`${BASE}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    history: history,
                    session_id: sessionId,
                    turn_number: turnNumber,
                    source_page: window.location.pathname
                })
            });
            const data = await res.json();
            hideTyping();

            const reply = data.response || 'Lo siento, no pude procesar tu mensaje.';
            addMessage('bot', reply);
            history.push({ role: 'assistant', content: reply });
        } catch (e) {
            hideTyping();
            addMessage('bot', 'Error de conexión. Por favor intenta de nuevo.');
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
        if (btn) sendMessage(btn.dataset.msg);
    });
})();
