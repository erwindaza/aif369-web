# Handoff — WhatsApp Agent Local (para Codex)

> Última actualización: 2026-10-03. Todo lo de este documento está implementado,
> desplegado en `agent01` y verificado (80/80 tests + simulaciones con LLM real).

---

## 0. Aclaración importante: NO se está entrenando ningún modelo

No hay fine-tuning, no se cambian pesos, no hay dataset de entrenamiento.

El modelo `gemma3:1b` (Ollama, local, ~0.5–3.6 s por llamada) **solo redacta la
respuesta final**. Todo el "razonamiento comercial" es **código determinista en
JavaScript**:

- extracción de datos con regex/reglas,
- estado de conversación en memoria (y JSONB en Postgres para sobrevivir reinicios),
- grafo de nodos con ramas fijas,
- validador determinista que revisa cada respuesta antes de enviarla.

Lo que hacemos cuando una conversación real sale mal **no es entrenar**: es
corregir reglas, agregar un guard (validación) o mejorar el prompt (few-shot +
hint). Si el LLM insiste en fallar, el grafo cae a una **respuesta
determinista construida desde el conocimiento** (nunca inventa).

---

## 1. Qué es este sistema

Agente comercial de WhatsApp, 100% local, dos bots compartiendo un solo número:

| Bot | Tenant | Sitio | CTA |
|---|---|---|---|
| AIF369 | `aif369` | aif369.com | calendly.com/edaza-aif369/30min |
| PriceClima | `priceclima` | priceclima.com | priceclima.com/contacto |

- Directorio: `whatsapp-agent-local/` (dentro del repo `aif369-web`, rama `features_bigpickle`; carpeta **untracked**, no commiteada aún).
- Conexión WhatsApp: **Baileys**, sesión ya vinculada. Jamás borrar `data/auth` ni regenerar QR.
- LLM: Ollama `gemma3:1b`, `num_predict=110`, `OLLAMA_TIMEOUT_MS=12000`, `CONTEXT_MESSAGES=12`.
- Base de datos: Postgres (`contacts`, `leads`, `opportunities`, `messages`, `conversation_state` JSONB).
- Knowledge: `knowledge/{tenant}/*.md` → retrieval **lexical** (0–4 ms).
- API local: `http://127.0.0.1:8090` (`/health`).

---

## 2. Arquitectura: qué pasa en cada mensaje

```
mensaje entrante (Baileys)
  → extract_message      src/extract.js        intents, slots, rechazo, fricción, "pendiente"
  → update_state         src/conversation-state.js  ConversationState + new/confirmed slots
  → detect_intent        src/intents.js + src/router.js  workflow sales|faq, route, decision
  → calculate_missing    src/slot-registry.js  missing_slots / next_slot / asked_slots
  → route                sales (pregunta del tenant) | faq (RAG)
  → next_slot | rag      composición determinista o retrieval (src/knowledge.js)
  → generate_response    src/agent.js + src/prompt.js → Ollama  (o state_machine sin LLM)
  → response_validator   src/response-validator.js      ≤1 pregunta, no repetir slot
                         conocido, precio solo si está en contexto, si preguntaron
                         por plata hay que citar montos; reintenta con hint y si
                         no cae a priceSummary() o respuesta determinista
  → contact footer       src/contact.js        pie con web/wa/email/CTA "solo cuando aporta"
  → finalizeTurn         src/index.js          qualifications + leads/opportunities en PG
```

**Regla de oro:** la rama `sales` es 100% determinista (sin LLM). La rama `faq`
usa RAG + LLM. Cotización (`QUOTE_REQUEST`) va al LLM con el conocimiento para
que cite precios reales (`src/router.js`).

Estado por conversación (`conversation-state.js`): `known_slots`, `asked_slots`,
`asked_counts`, `intents`, `active_intent`, `pendingSlot`, `new_slots`,
`confirmed_slots`, `added_intents`, `frustration_score`,
`frustration_this_turn`, `rejection_this_turn`, `conversation_summary`.

---

## 3. Qué se hizo en esta última fase (todo implementado y verificado)

Objetivo: corregir lo que salió mal en una conversación real por WhatsApp.

### 3.1 Rechazo y handoff no se detectaban
- `src/intents.js`: regla `HUMAN` ampliada → `dame con|pásame con|tu manager|jefe|gerente|persona real|mala manera|mal atendido|atender…(persona|humano)`.
- `src/contact.js`: triggers del pie ampliados con `deriv|humano|manager`.

### 3.2 "No, yo solo quiero un aire acondicionado" se tomaba como slot
- `src/extract.js`:
  - `REJECTION_RE` + `detectRejection()` (líneas 31–34): `solo quiero…`, `no…quiero|busco|me interesa`, `no es eso`, `olvídalo`.
  - El rechazo cortocircuita el extractor (línea 85): no extrae slots de ese mensaje.
  - `FRICTION_LEAD_RE` (línea 39): `ya te dije…` se recorta antes de extraer.
  - `isEmpresaName()` (línea 49) + `EMPRESA_STOP` (desde `qualification.js`) para que verbos ("somos de") no se guarden como nombre de empresa.
  - `EMPRESA_SIGNAL_RE`: mensajes que hablan de empresa no se asignan a `pendingSlot`.
  - `extractDeterministic(..., pendingSlot)` (línea 81): si el turno anterior terminó con una pregunta, el texto sin `?` se asigna al slot pedido — con bloqueos (`blocked` línea 144): no si hay otro slot requerido/contacto extraído, si hay `reconfirmed`, si hay intent nuevo (priceclima) o si habla de empresa.
  - `reconfirmed` se calcula con `extractQualification(value, {})` (atribución limpia de aif369).
  - `extractMessage()` acepta `pendingSlot` y propaga `rejection` / `reconfirmed`.

### 3.3 Respuestas idénticas y tono rudo ("no lo repitas")
- `src/conversation-state.js`:
  - `FRICTION_PATTERNS` (línea 15) incluye `ya te di `.
  - `composeMissingSlotReply()` (línea 288) ahora dice **una sola cosa por turno**:
    - `Entonces buscas X.` solo si `added_intents` (intents realmente nuevos este turno);
    - `Disculpa, ya me habías dicho X.` solo en el turno de fricción (`frustration_this_turn`) y sin duplicar confirmados (`knownFact`, línea 267, prefiere el valor citado en el mensaje del usuario);
    - `Perfecto, anoto …` solo con `new_slots` (dedupe por valor + slots requeridos primero);
    - `Perfecto, … ya lo tengo.` para `confirmed_slots`;
    - sin cambios → solo la pregunta.
  - `composeClarifyReply()` (línea 344) y `composeCreateLeadReply()` (línea 350).
  - `applyExtraction()` (línea 160) calcula `new_slots / confirmed_slots / added_intents / asked_counts / frustration_this_turn / rejection_this_turn`.
  - `determineNextAction()` (línea 149): `ctx.rejection → clarify_intent` (después del handoff no, el handoff gana).

### 3.4 Grafo: ramas nuevas y pregunta controlada
- `src/graph.js`:
  - `pendingSlotFor` en extract (línea 88) **con re-ejecución**: si el estado fresco no tenía pendiente y la extracción salió vacía, se re-extrae con el pendiente nuevo (línea 101).
  - Ramas deterministas `clarify_intent` (línea 161) y `create_lead` (línea 170): `ctx.generated=false`, `ctx.question=null` o `contacto`.
  - `expectQuestion` solo para `ask_missing_slot | answer_question | recover_conversation` (línea 217).
  - `markAsked()` (línea 330) incrementa `asked_counts`.
  - Hint de precios en el primer intento de LLM (línea 206).
  - `TEMPLATE_REPLY` actualizado (no más "no lo repitas").

### 3.5 Validador
- `src/response-validator.js`:
  - `norm()` colapsa `_` (evita falsos positivos de pregunta repetida).
  - `validateResponse()` (línea 50): `empty`, `multiple_questions`, `question_about_known_slot`, `repeated_question`, `missing_next_question`, `invented_price`, **`prices_not_cited`** (línea 96), `friction_not_acknowledged`.
  - `extractPrices` acepta `$319.990`, `$3,000`, `$250`; `priceKey` normaliza coma/punto (no acusa invento por formato).
  - `repairHint()` (línea 108) traduce issues a instrucciones de reintento.
  - `priceSummary()` (línea 126): si el LLM no citó montos, arma la respuesta con frases del conocimiento que contengan `$` (máx 2, 10–300 caracteres). **No inventa.**
  - `deterministicReply()` (línea 137) respeta la acción (`clarify_intent` / `create_lead`).

### 3.6 Router / cotización
- `src/router.js`: `QUOTE_REQUEST` → LLM (el `QUOTE_REPLY` instantáneo ya no se usa).
- `src/slot-registry.js`: `slotQuestion()` (línea 194) rota variantes por `asked_counts` (`times % ask.length`), retrocompatible con `askCount=null`.
- `src/qualification.js`: `EMPRESA_STOP` exportado; `EMPRESA_KEYWORDS` ordenado largo→corto (`somos de` antes que `somos`); `URGENCY_SOFT_RE` sin `ya` suelto (añadió `ya mismo`).
- `src/index.js`: `finalizeTurn` con `forceLead`/`leadIntent` (líneas 327–330); la oportunidad se crea también cuando `result.action === 'create_lead'` aunque la ruta no marque `lead`.

### 3.7 Footer de contacto
- `src/contact.js`: `withContactFooter()` solo cuando aporta (agendar, cotizar, servicios, precios, contacto, handoff, saludo, knowledge_guard, fallback), nunca duplica links ya escritos, y el mismo bloque viaja en el prompt (`contactMessage` en `src/prompt.js`).
- Contacto compartido: WhatsApp `https://wa.me/56997547192`, `edaza@aif369.com`.
- **Discrepancia abierta**: `knowledge/priceclima/company.md` publica `+56 9 8484 0331` vs el pie `9754 7192`. Falta decidir cuál es el correcto.

---

## 4. Tests

- Framework: `node --test` (nada de Jest). `npm test`.
- **80/80 pasan local y en agent01.**
- Archivos clave:
  - `test/recovery-flow.test.js` — handoff manager, rechazo→clarify sin LLM, atribución aif369/priceclima, no repetir resumen, tono un solo turno, create_lead, trigger de pie, dato repetido→confirmado, rotación de variantes.
  - `test/response-validator.test.js` — `prices_not_cited`, separadores de precio, monto inventado, `priceSummary`, `deterministicReply` por acción.
  - `test/priceclima-conversation.test.js` — flujo priceclima (`ya me habías dicho un dormitorio`, sin `no lo repitas`).
  - `test/router.test.js` — cotización → `llm: true`.
- En agent01 la salida TAP usa `# tests` (no `ℹ`): usar `node --test 2>&1 | grep -E "^# (tests|pass|fail)"`.
- **Importante**: local NO existe `gemma3:1b` (Ollama 404). Los tests locales usan dependencias inyectadas (`rulesExtract`), no Ollama.

---

## 5. Simulaciones hechas con LLM real en agent01 (evidencia)

Secuencia aif369 (`node scripts/simulate.mjs "De parte de bejoby" "Necesito la arquitectura medallion..." "Un etl" "¿Y precios tienes?" "No yo solo quiero un aire acondicionado" "Dame con tu manager"`):

1. `ask_missing_slot` → "Entonces buscas proyecto de datos e IA. Perfecto, anoto empresa: bejoby. ¿Cual es el principal problema…?" (valid=ok)
2. `ask_missing_slot` → anota problema, pide fuentes (valid=ok)
3. `create_lead` → "…¿Me dejas un email o telefono…?" (valid=ok)
4. `route=cotizacion` → primer intento falla `prices_not_cited` → retry con hint → cita `$4.000–$8.000 USD` (valid=ok)
5. rechazo → `clarify_intent` → "Disculpa si me pasé con las preguntas. ¿Seguimos por aquí o prefiero que te derive…?" (valid=ok)
6. manager → `route=human_handoff`, `llm=false`, instant_rule + footer (valid=ok)

Priceclima (`node scripts/simulate.mjs --tenant priceclima`): 8/8 valid=ok,
incluye "Disculpa, ya me habías dicho un dormitorio. ¿Cuántos equipos son en total?"
y "¿Cuánto cuesta la mantención?" → `$199.990` / `$39.990` del knowledge al primer intento.

Métricas (`npm run leads`): latencia salida avg 1183 ms, p50 826 ms, max 2391 ms,
llm avg 456 ms, retrieval avg 0 ms.

---

## 6. Comandos (todos probados)

```bash
# --- desarrollo local ---
cd whatsapp-agent-local
npm test                                   # 80 tests (node --test), sin WhatsApp ni DB
node scripts/simulate.mjs "hola"                       # aif369 con LLM si está disponible
node scripts/simulate.mjs --tenant priceclima
node scripts/simulate.mjs --json "pregunta"            # JSON por línea '['
node scripts/simulate.mjs --no-llm --no-graph          # solo determinista

# --- deploy + verificar en agent01 ---
bash scripts/deploy.sh                    # rsync; excluye node_modules data runtime .env
ssh agent01 'export PATH=$HOME/.local/bin:$PATH && cd ~/whatsapp-agent && node --test 2>&1 | grep -E "^# (tests|pass|fail)"'
ssh agent01 'export PATH=$HOME/.local/bin:$PATH && cd ~/whatsapp-agent && kill $(cat runtime/manual-agent.pid); sleep 4; bash scripts/start-user-agent.sh; sleep 12; curl -s http://127.0.0.1:8090/health'
ssh agent01 'export PATH=$HOME/.local/bin:$PATH && cd ~/whatsapp-agent && node scripts/simulate.mjs --tenant priceclima 2>&1 | grep -E "\[graph\]|^(>>|===|route=|branch=)"'
ssh agent01 'export PATH=$HOME/.local/bin:$PATH && cd ~/whatsapp-agent && npm run leads'
ssh agent01 'export PATH=$HOME/.local/bin:$PATH && cd ~/whatsapp-agent && npm run latency'
```

- Remoto `agent01` = user `erwin`, app `~/whatsapp-agent`, log `runtime/manual-agent.log`, pid `runtime/manual-agent.pid`.
- `deploy.sh` imprime `npm install && sudo systemctl restart whatsapp-agent`, pero **el agente corre como proceso manual**: usar `start-user-agent.sh` (el systemd no existe).

---

## 7. Qué FALTA (para que Codex continúe)

Orden sugerido:

1. **Prueba manual por WhatsApp real** (lo único que no se puede simular):
   saludo → "de parte de bejoby" → problema → fuentes → "¿Y precios tienes?" →
   "No, yo solo quiero un aire acondicionado" → "dame con tu manager".
   Verificar en `npm run leads` que quedó 1 lead + oportunidad + handoff.
2. **Teléfono de priceclima**: decidir si el pie usa 9754 7192 o el 8484 0331
   publicado en `knowledge/priceclima/company.md` y unificar.
3. **Footer en respuestas de precio**: si la respuesta es solo montos sin la
   palabra "precio/cotizar", el pie no aparece (`CONTACT_TRIGGER` evalúa solo
   la respuesta). Evaluar disparar también con el mensaje del usuario.
4. **Commit**: la carpeta `whatsapp-agent-local/` está untracked. Si se pide,
   commitear en `features_bigpickle` (nunca en `main`).
5. **Gemini como LLM** (anotado como futuro): backend `/api/chat`,
   `SYSTEM_PROMPT` del widget `chat-widget.js`. Hoy todo pasa por Ollama.
6. **Posibles mejoras de calidad** (baja prioridad, ya funcionan):
   - `priceSummary` a veces responde con frases algo entrecortadas (2 frases del conocimiento unidas).
   - El 1B a veces omite el precio en el primer intento (el guard lo corrige con retry).
   - `asked_counts` no degrada si el usuario cambia de tema y vuelve.

---

## 8. Reglas duras (NO violar)

Del `AGENTS.md` del repo (zero-trust de producción):

- Push directo a `main`: prohibido. Ruta: `feature → dev → qa → PR qa→main → aprobación humana (Erwin) → producción`.
- Los agentes NO aprueban ni mezclan PRs de producción, NO corren `gcloud run deploy` ni `terraform apply` de producción.
- Nada de secretos en Git, `.env`, logs ni reportes. Secret managers aprobados.
- En este agente: **no borrar `data/auth`, no re-vincular QR, no mezclar tenants de marca** (aif369 y priceclima comparten número pero nunca conocimiento ni tono).
- Los precios SIEMPRE salen de `knowledge/`. El guard `invented_price` es la última línea de defensa; no desactivarlo.
