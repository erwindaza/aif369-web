# AIF369 WhatsApp Agent — 100% local (agent01)

Agente comercial de WhatsApp que atiende clientes de [aif369.com](https://aif369.com) **sin que la data salga de la red local**.

| Componente | Tecnología | Dónde corre |
| --- | --- | --- |
| Canal WhatsApp | **Baileys 6.7.24** (WhatsApp Web, vinculación por QR) | agent01 (Lenovo Legion) |
| Base de datos de clientes | PostgreSQL 18 local | agent01 |
| Motor de respuesta | Ollama `gemma3:1b` | agent01 |
| Orquestación | Node.js 22 (un solo proceso) | agent01, proceso de usuario (`manual-agent.pid`) |
| Healthcheck | HTTP nativo en `127.0.0.1:8090` | agent01 |

Nada de esto toca la nube: ni Meta Cloud API, ni Gemini, ni GCP.

## Ubicación de la sesión WhatsApp (FASE 2)

- **Librería:** `@whiskeysockets/baileys` (`package.json`).
- **Persistencia:** `/home/erwin/whatsapp-agent/data/auth/` (`creds.json`, `pre-key-*.json`, `app-state-sync-*.json`).
- Permisos: propiedad de `erwin`, dentro del home (no `/tmp`, no volátil). Sobrevive reinicios del servicio y del servidor.
- Regla: **no borrar `data/auth/` salvo demostración de corrupción** (borrarlo obliga a escanear QR de nuevo).
- QR pendiente (solo mientras hay pairing): `runtime/whatsapp-qr.png`; se elimina al autenticar.

## Estados del agente (FASE 10)

Logs con `[whatsapp] state=<ESTADO>`:

`STARTING → AUTHENTICATING → WAITING_FOR_QR → CONNECTED → READY`, más `DISCONNECTED`, `DEGRADED`, `ERROR`.

## Arquitectura (agente comercial)

```
WhatsApp Transport (src/whatsapp.js)
      ↓  mensaje normalizado (src/normalize.js: chat_jid/chatJid a nivel superior)
Conversation Service (src/index.js + src/db.js)   ← dedupe idempotente, upsert de contacto
      ↓
Router determinístico (src/router.js, respuesta según tenant)
      ├── meta guard / opt-out / handoff / retomar bot / estado / ping
      ├── saludo y agenda (respuestas fijas, sin LLM); cotización → retrieval/LLM con precios del knowledge
      ├── recepción multiagente (Erwin Androide) y ruteo experto por dominio
      └── clasificación de intención (src/intents.js: 12 intents)
      ↓
Grafo conversacional (src/graph.js, un turno = un recorrido)
      extract_message      → extracción determinista de intents/slots (src/extract.js)
      update_state         → ConversationState en memoria + fricción (src/conversation-state.js)
      detect_intent        → workflow sales|faq
      calculate_missing_slots → missing_slots / next_slot / asked_slots
      route                → sales (sin signo de interrogación) | faq (pregunta)
      next_slot | rag      → respuesta determinista o Knowledge/Retrieval (src/knowledge.js)
      generate_response    → state_machine o Agent (src/agent.js + src/prompt.js + Ollama)
      response_validator   → ≤1 pregunta, no repite slot conocido, precio solo si está en el
                             contexto, y si el cliente pregunta por plata la respuesta debe
                             citar montos del conocimiento; reintenta con nota y si no cae a
                             frases del conocimiento o a respuesta determinista
      ↓
Qualification + Leads (src/qualification.js) → contacts/leads/opportunities en PostgreSQL
      + conversation_state (JSONB por conversación: el estado sobrevive reinicios)
      ↓
Outbound (envío inmediato para reglas; encolado con retrieval+LLM para el resto)
```

Cada turno queda en `messages` con `retrieval_ms`, `llm_ms` y `total_ms`; el resumen del contacto (`lead_status`, `summary`, `qualification`) se actualiza en `contacts` y la oportunidad abierta en `opportunities`.

### Estados de lead

`NEW → QUALIFYING → QUALIFIED / HOT → (HUMAN_HANDOFF | CLOSED)`. Score 0-100 (`hot ≥ 70`). El handoff deja el turno en espera (`held_for_human`) hasta que alguien responde o el cliente escribe `bot`.

### Estado conversacional (ConversationState)

Por conversación se persiste un `ConversationState` (`conversation_state.state` JSONB): `intents`, `known_slots`, `missing_slots`, `asked_slots` + `asked_counts`, `new_slots`, `confirmed_slots`, `added_intents`, `friction_score`, `frustration_detected`, `frustration_this_turn`, `rejection_this_turn`, `next_slot`, `next_action`. Cada turno:

1. **Extracción** determinista primero (regex del `src/slot-registry.js`, acotadas por intent); el LLM (`chatJson`, `EXTRACTOR=auto|rules|model`) solo entra si no encontró nada. Nunca escribe slots que el usuario no entregó. Si lo que se preguntó sigue vacío y la respuesta es texto plano (sin `?`, sin sí/no cortos ni rechazo), va al **slot pendiente**: "De parte de bejoby" responde `empresa`, "Un etl" responde `fuentes`. Un mensaje que aporta otro campo requerido, declara un intent nuevo o habla de la empresa no se atribuye al pendiente.
2. **Rechazo**: "No, solo quiero X" / "olvídalo" → `clarify_intent` con respuesta corta que ofrece seguir o derivar con una persona, sin insistir con el formulario.
3. **Fricción**: patrones tipo "ya te dije" → `recover_conversation`, que reconoce el dato repetido **ese turno** ("Disculpa, ya me habías dicho X.") y nunca vuelve a aparecer en los turnos siguientes.
4. **Respuesta de la rama sales**: se arma solo con lo que cambió en este turno (`added_intents` → "Entonces buscas …", `new_slots` → "Perfecto, anoto …", `confirmed_slots` → "… ya lo tengo"). Sin cambios nuevos, la respuesta es únicamente la pregunta, con variante rotada según `asked_counts`.
5. **Siguiente slot**: `missing_slots` ordenados por avance del intent y recencia, saltando los ya `asked_slots`.
6. **Cierre**: con todos los requeridos completos → `create_lead` determinista: pide `contacto` una sola vez y si ya está, cierra con "Preparo la propuesta y te aviso por aquí."
7. **Validador**: una sola pregunta por respuesta, no pregunta lo ya conocido, no repite `asked_slots`, precios solo si están en el contexto; si falla reintenta con nota y si vuelve a fallar responde de forma determinista.

Variables de la fase de estado: `GRAPH_ENABLED=0` vuelve al pipeline anterior (sin grafo), `EXTRACTOR=auto|rules|model` elige la extracción de slots, `TENANT` el bot por defecto.

### Agentes expertos (tenants)

`src/tenants.js` define los agentes `personal`, `aif369`, `priceclima`,
`bejoby` y `pricescrapers` con marca, saludo, prompt/knowledge
(`knowledge/<tenant>/`) y registro de slots. Cada agente tiene un contrato en
`agents/<tenant>/AGENTS.md`; la política común está en
`agents/OPERATING_POLICY.md`.

Antes de responder, `src/expert-router.js` infiere el dominio:

- `PriceClima.com`: aire acondicionado, climatización, instalación, mantención y obras relacionadas.
- `AIF369.com`: Data, IA, agentes, ETL/ELT, gobierno y proyectos de implementación.
- `Bejoby`: talento TI y coaching.
- `PriceScrapers`: desarrollo full stack, scraping, APIs e integraciones.
- `Personal`: mensajes para Erwin; el bot no impersona a Erwin.
- `Accountant`: calculos, compras, ventas, proveedores y validacion de cotizaciones.

Si el número no es conocido o el tema es ambiguo, el saludo de recepción es
neutral: "Hola, habla Erwin Androide. ¿Con quién tengo el gusto y en qué te
puedo ayudar?". Si el usuario escribe en inglés, responde en inglés.

```bash
npm run simulate -- --tenant priceclima     # conversación de climatización
TENANT=priceclima npm run simulate          # otro bot completo
```

### Contacto y links en las respuestas

`src/contact.js` agrega un pie corto con datos de empresa **solo cuando aporta**:
agenda, contacto, llamada, asesor, visita, compra, garantía o derivación humana.
No se fuerza en saludo, cotización ni handoff para evitar spam de firma.
Opt-out, ping y estado técnico no lo llevan y nunca se duplica un link ya
escrito. El mismo bloque viaja en el prompt (`contactMessage` en
`src/prompt.js`) para que el modelo cite links reales cuando corresponde.

Los agentes comerciales atienden desde el mismo número operativo
(+56 9 9754 7192). Para AIF369, las cotizaciones se preparan como draft antes
de enviarse desde `edaza@aif369.com`; copiar a Erwin personal requiere
confirmación de la casilla configurada.

### Cotizaciones y aprobacion

El flujo correcto de cotizacion es:

1. El agente comercial califica la oportunidad.
2. `agent02` o el agente backoffice prepara el borrador.
3. El agente `Accountant` valida los calculos con logica deterministica, no con
   texto generado por LLM. Las operaciones permitidas incluyen suma, resta,
   multiplicacion, division, porcentajes, redondeos, subtotal, descuento,
   impuestos y total.
4. Se envia primero un email interno a Erwin con subject del tipo:
   `[BORRADOR REVISION] <cliente> - <tipo de cotizacion>`.
5. El cuerpo debe indicar que es una cotizacion borrador para revision previa a
   la cotizacion comercial real.
6. Solo despues de aprobacion por email, WhatsApp o estado manual aprobado, el
   agente puede preparar el envio al cliente final desde Zoho Mail
   `edaza@aif369.com`.
7. Para trabajos con compras o proveedores, pedir y registrar cotizaciones de
   proveedores antes de comprometer precio final al cliente.

Tablas relacionadas:

- `quote_calculations`: line items, formulas, subtotales, descuentos, impuestos y total validado.
- `quote_approvals`: solicitud y decision de aprobacion interna.
- `outbound_email_queue`: emails internos, emails al cliente y solicitudes a proveedores.

### Conocimiento

`knowledge/aif369/*.md` y `knowledge/priceclima/*.md` con encabezados `##` y `<!-- fuente: ... -->`. Se recargan en cada arranque (caché en memoria). Opcional: `KNOWLEDGE_RETRIEVER=embedding` usa `nomic-embed-text` con caché en `runtime/knowledge-embeddings.json` (hoy corre `lexical`, 0-4 ms).

**Guardia de alucinación:** si el retrieval devuelve 0 fragmentos y el mensaje tiene 20+ caracteres, el LLM no se invoca: responde `knowledge_guard` ("No tengo ese dato confirmado…") + pregunta de calificación. Así un modelo de 1B no puede inventar servicios ajenos (aire acondicionado, SEO, etc.).

## Healthcheck (FASE 11)

```bash
curl -s http://127.0.0.1:8090/health
# {"status":"ok","whatsapp":"READY","database":"ok","signal_errors":0,...}
curl -s http://127.0.0.1:8090/ready
```

`/ready` devuelve 503 si WhatsApp no está READY o la base no responde.

## Modelo de datos (FASE 8)

| Tabla / vista | Contenido |
| --- | --- |
| `contacts` | jid, teléfono, nombre, intent, `hot_lead`, `human_handoff`, contador |
| `messages` | `chat_jid` + `msg_id` (**PK compuesta = idempotencia**), `direction`, `body`, `intent`, `route`, `model`, `latency_ms`, `processing_status` (`received`/`sent`/`ignored`), `created_at` |
| `conversations` (vista) | agrupación por conversación con inbound/outbound/última actividad |
| `events` | auditoría local: `hot_lead`, `handoff_on/off`, `duplicate_ignored`, `unsupported_type`, `held_for_human` |

Idempotencia (FASE 9): `INSERT ... ON CONFLICT DO NOTHING` sobre la PK; un `message_id` repetido se registra como `duplicate_ignored` y no vuelve a actuar el negocio.

## Errores Bad MAC (FASE 4)

Provienen de `libsignal/src/session_cipher.js:157` (`console.error` + `SessionError`) cuando el dispositivo recibe mensajes cuyas sesiones Signal no existen aún. Causa típica: historial encolado antes/durante el primer pairing y re-vinculaciones sucesivas (varios QR). Son **transitorios y recuperables**: no afectan `creds.json` ni impiden recibir mensajes nuevos.

Mitigación en `src/signal-guard.js`: filtra el flood de stack traces y emite `[whatsapp][warn] message decryption failed (recuperable, total=N)` cada 30 s; el contador se expone en `/health.signal_errors`. No se imprimen claves, tokens ni QR raw. No se borra la sesión.

## Operación

Proceso de usuario (no systemd): pid en `runtime/manual-agent.pid`, log en `runtime/manual-agent.log`.

```bash
ssh agent01 'export PATH=$HOME/.local/bin:$PATH'
cd ~/whatsapp-agent
bash scripts/start-user-agent.sh          # arranca si no corre
kill $(cat runtime/manual-agent.pid)      # detiene (3 s) y vuelve a arrancar
tail -f runtime/manual-agent.log
curl -s http://127.0.0.1:8090/health
npm run leads                             # leads + oportunidades + handoffs + latencias
npm run worker:proposals                  # agent02: crea jobs y borradores de propuesta
npm run worker:drafts                     # lista borradores comerciales para revision
npm run worker:start                      # loop continuo para agent02
npm run chat -- "<jid>@s.whatsapp.net"    # historial de una conversación
npm run latency                           # percentiles de retrieval/llm/total
```

Nunca borrar `data/auth/` ni re-vincular QR: eso obliga a escanear de nuevo desde el teléfono.

## Seguridad (FASE 15)

`.gitignore` excluye `.env`, `data/` (sesión WhatsApp), `runtime/` (QR), `sessions/`, `tokens/`, `.auth/`, `*.session`. Los logs no incluyen tokens, claves Signal, credenciales de PostgreSQL ni el payload crudo del QR (solo la representación ASCII/PNG necesaria para vincular).

## Desarrollo

```bash
npm test                                   # 80 tests (node --test), sin WhatsApp ni DB
npm run simulate                           # casos A-F por la tubería completa (sin DB)
npm run simulate -- --no-llm               # solo reglas + grafo determinista
npm run simulate -- --tenant priceclima    # transcripción de climatización
npm run simulate -- --no-graph "hola"       # pipeline anterior (sin grafo)
node scripts/bench-ollama.mjs              # latencia por modelo
npm run worker:proposals                   # crea/consume jobs de propuesta para agent02
npm run worker:drafts                      # revisa drafts listos

bash scripts/deploy.sh                     # rsync a agent01 (no toca data/ ni .env)
ssh agent01 'cd ~/whatsapp-agent && kill $(cat runtime/manual-agent.pid)' && sleep 3
ssh agent01 'cd ~/whatsapp-agent && export PATH=$HOME/.local/bin:$PATH && bash scripts/start-user-agent.sh'
```

Pendiente (futuro): usar Gemini vía el backend (`/api/chat` de `backend/main.py`, mismo `SYSTEM_PROMPT` del widget web) cuando el cliente busque productos de aif369.com; hoy el agente WhatsApp responde 100% local con Ollama.

Setup desde cero: `scripts/setup-agent01.sh` (con sudo interactivo) o `printf '<pw>' | sudo -S bash scripts/setup-sudo.sh` (solo operaciones root).

## Agent02: worker de propuestas

`agent02` no atiende WhatsApp. Consume `worker_jobs` desde la misma base local de
`agent01` via tunel SSH y deja borradores en `sales_drafts`. También puede
usarse como apoyo para consultas de base de datos, contexto de oportunidades,
precios, drafts y reglas de negocio antes de que `agent01` responda o antes de
enviar una cotización.

Servicios systemd en `agent02`:

```bash
sudo systemctl status aif369-db-tunnel-agent02.service
sudo systemctl status aif369-sales-worker-agent02.service
sudo journalctl -u aif369-sales-worker-agent02.service -n 80 --no-pager
cd ~/whatsapp-agent && npm run worker:drafts
```

El tunel escucha solo en `127.0.0.1:15432` dentro de `agent02` y apunta a
`127.0.0.1:5432` en `agent01`. No abrir Postgres a la red local.

## Recuperación de sesión

```bash
# diagnostico no destructivo:
ssh agent01 'cd ~/whatsapp-agent && curl -s http://127.0.0.1:8090/health'
ssh agent01 'cd ~/whatsapp-agent && tail -n 80 runtime/manual-agent.log'
```

No borrar `data/auth/` como primer paso. Si se demuestra corrupcion real de
sesion, respaldar el directorio y pedir aprobacion humana explicita antes de
resetear el QR.
