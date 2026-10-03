# AIF369 Database Catalog

## Alcance

Este documento inventaria las bases de datos y tablas activas del proyecto
AIF369, incluyendo analitica cloud, ventas, pagos, cumplimiento, programa
educativo y la base local del agente WhatsApp.

El objetivo de datos para ventas es simple:

```text
canal -> conversacion -> lead -> oportunidad -> job agentico -> borrador -> revision humana -> cierre
```

## Plataformas de Datos

| Plataforma | Uso principal | Ambiente | Fuente |
| --- | --- | --- | --- |
| BigQuery | Analitica, formularios, scorecards, chats, pagos, CRM, ARCO | dev / qa / prod | `backend/main.py`, `infra/terraform/bigquery_tables.tf`, `backend/schema_*.sql` |
| Firestore | Estado operacional de baja latencia: accesos pagados e idempotencia WhatsApp | dev / qa / prod | `backend/main.py` |
| PostgreSQL local | Operacion local del agente WhatsApp con Baileys/Ollama en `agent01` | local | `whatsapp-agent-local/schema.sql` |
| PostgreSQL Master | Programa educativo, lecciones, labs, alumnos, evaluaciones | local/servicio agentes | `aif369-agents/db/schema.sql` |

## Ambientes

| Ambiente | Proyecto/Dataset esperado | Regla |
| --- | --- | --- |
| DEV | `aif369-backend.aif369_analytics_dev` | Desarrollo y pruebas funcionales |
| QA | `aif369-backend.aif369_analytics_qa` o dataset QA equivalente | Validacion antes de produccion |
| PROD | `aif369-backend.aif369_analytics` | Solo despues de PR aprobado y merge humano |

No se deben ejecutar cambios productivos directos desde agentes. Produccion se
promueve por PR `qa -> main` con aprobacion humana.

## BigQuery: Modelo Operacional y Analitico

### `contact_form_submissions`

Fuente: `infra/terraform/bigquery_tables.tf`, escrituras en `backend/main.py`.

Uso:
- formularios de contacto;
- educacion/cursos;
- inscripciones legacy;
- pagos de servicios de consultoria guardados como evento comercial;
- fallback de scorecard si falla la tabla dedicada.

Campos principales:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `submission_id` | STRING | ID unico |
| `timestamp` | TIMESTAMP | Fecha del evento |
| `name` | STRING | Nombre entregado por usuario |
| `email` | STRING | Email del lead/cliente |
| `company` | STRING | Empresa o curso/servicio en flujos legacy |
| `role` | STRING | Cargo o clasificacion del flujo |
| `message` | STRING | Mensaje o resumen del evento |
| `source_page` | STRING | Pagina/formulario origen |
| `user_agent` | STRING | Navegador |
| `ip_address` | STRING | IP recibida |
| `form_type` | STRING | `contact`, `education`, `scorecard`, `consulting_payment`, etc. |
| `interest` | STRING | Interes declarado |
| `team_size` | STRING | Tamano de equipo |

Particion:
- `DAY` por `timestamp`.

Clustering:
- `email`, `timestamp`.

Observacion de ingenieria de datos:
- Esta tabla mezcla varios dominios. Debe mantenerse como bronze historico, no
  como fuente unica de verdad del CRM.

### `scorecard_submissions`

Fuente: `infra/terraform/bigquery_tables.tf`, endpoint `/api/scorecard`.

Uso:
- madurez AI Readiness;
- senales de lead calificado;
- insumo para recomendaciones comerciales.

Campos principales:
- `submission_id`, `timestamp`, `name`, `email`, `company`, `role`;
- `total_score`, `maturity_level`, `maturity_number`;
- `dimensions_json`, `answers_json`;
- `source_page`, `user_agent`, `ip_address`.

Particion:
- `DAY` por `timestamp`.

Clustering:
- `email`, `maturity_level`.

### `chat_conversations`

Fuente: `infra/terraform/bigquery_tables.tf`, `save_chat_to_bigquery`.

Uso:
- conversacion web y WhatsApp Cloud API;
- memoria historica para agentes;
- analitica de intenciones y conversion.

Campos principales:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `message_id` | STRING | ID unico del mensaje/intercambio |
| `session_id` | STRING | Agrupa conversacion |
| `timestamp` | TIMESTAMP | Fecha del turno |
| `user_message` | STRING | Mensaje usuario |
| `assistant_response` | STRING | Respuesta IA |
| `provider` | STRING | `gemini`, `ollama`, `crm_quote_agent`, `safe_fallback`, etc. |
| `turn_number` | INTEGER | Turno de conversacion |
| `source_page` | STRING | `whatsapp`, web page, etc. |
| `user_agent` | STRING | Cliente/origen |
| `ip_address` | STRING | IP cuando aplique |
| `language` | STRING | `es`, `en` |
| `intent_detected` | STRING | Intencion detectada |

Campos escritos por codigo que no aparecen en Terraform actual:
- `input_tokens`;
- `output_tokens`;
- `origin_header`;
- `suspicious`.

Accion recomendada:
- alinear Terraform con el contrato real de `backend/main.py` para evitar
  errores de insercion por esquema incompleto.

### `chat_session_metadata`

Fuente: `backend/schema_metadata.sql`, `save_chat_metadata`.

Uso:
- metadata comercial de una sesion;
- lead scoring;
- pipeline desde chat.

Campos principales:
- `session_id`;
- `metadata_timestamp`;
- `user_role`;
- `industry`;
- `project_status`;
- `lead_quality_score`;
- `lead_source`;
- `qualification_stage`;
- `whatsapp_shared`;
- `email_captured`;
- `company_name`;
- `created_at`, `updated_at`.

Vista:
- `chat_lead_pipeline`.

Riesgo actual:
- `ensure_metadata_table()` crea una version reducida de la tabla si no existe.
  Esa version no incluye todos los campos declarados en `schema_metadata.sql`.

Accion recomendada:
- manejar esta tabla con migracion SQL/Terraform, no con creacion parcial al
  inicio del backend.

### `crm_agent_quotes`

Fuente: `backend/schema_crm_agent.sql`, `build_sales_quote_response`.

Uso:
- cotizaciones referenciales generadas por el agente;
- pipeline comercial;
- estimacion de ticket.

Campos principales:
- `quote_id`, `created_at`, `session_id`, `source_page`;
- `service_key`, `service_label`;
- `user_message`;
- `currency`, `estimated_min`, `estimated_max`;
- `complexity_multiplier`;
- `assumptions_json`;
- `crm_context_json`;
- `stage`;
- `ip_address`.

Vistas:
- `crm_agent_quotes_silver`;
- `crm_agent_quote_pipeline_gold`.

Particion:
- `DAY` por `created_at`.

Clustering:
- `service_key`, `stage`, `session_id`.

Accion recomendada:
- parametrizar `PROJECT_ID` y `DATASET_ID`. El SQL actual usa dataset productivo
  literal en `schema_crm_agent.sql`.

### `sales_opportunities`

Fuente: `backend/schema_sales_opportunities.sql`.

Uso:
- entidad canonica de ventas;
- une formularios, web chat, scorecards, WhatsApp Cloud, WhatsApp local,
  cotizaciones y pagos;
- fuente principal para pipeline comercial.

Grano:
- una oportunidad comercial por necesidad/proceso/servicio identificado.

Campos principales:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `opportunity_id` | STRING | ID unico de oportunidad |
| `created_at` | TIMESTAMP | Fecha de creacion |
| `updated_at` | TIMESTAMP | Ultima actualizacion |
| `environment` | STRING | dev/qa/prod |
| `source_channel` | STRING | `web_form`, `web_chat`, `scorecard`, `whatsapp_cloud`, `whatsapp_local`, `payment`, `manual` |
| `source_system` | STRING | Sistema origen: backend, Meta, Baileys, PayPal, etc. |
| `source_record_id` | STRING | ID origen: submission, message, quote, order, event |
| `session_id` | STRING | Sesion conversacional si aplica |
| `trace_id` | STRING | Trazabilidad agentica |
| `contact_hash` | STRING | Hash de contacto para canales sin email o con telefono |
| `email` | STRING | Email cuando el usuario lo entrega |
| `display_name` | STRING | Nombre visible |
| `company_name` | STRING | Empresa |
| `role` | STRING | Rol/cargo |
| `industry` | STRING | Industria |
| `service_key` | STRING | Servicio ofertado |
| `service_label` | STRING | Nombre comercial del servicio |
| `stage` | STRING | `new`, `qualified`, `proposal`, `scheduled`, `won`, `lost`, `nurture`, `handoff` |
| `lead_score` | INT64 | 0-100 |
| `intent` | STRING | Intencion detectada |
| `pain_point` | STRING | Dolor principal |
| `urgency` | STRING | Urgencia |
| `budget_range` | STRING | Rango declarado |
| `next_action` | STRING | Proxima accion |
| `owner` | STRING | Responsable |
| `human_handoff` | BOOL | Requiere humano |
| `currency` | STRING | Moneda |
| `estimated_min` | NUMERIC | Minimo estimado |
| `estimated_max` | NUMERIC | Maximo estimado |
| `expected_value` | NUMERIC | Valor esperado |
| `probability` | FLOAT64 | Probabilidad 0-1 |
| `last_message` | STRING | Ultimo mensaje relevante |
| `notes` | STRING | Notas |
| `metadata_json` | STRING | Payload flexible |

Vistas:
- `sales_opportunities_silver`;
- `sales_pipeline_gold`;
- `sales_opportunity_sources_gold`.

Particion:
- `DAY` por `created_at`.

Clustering:
- `source_channel`, `stage`, `service_key`, `contact_hash`.

Regla de privacidad:
- no guardar telefono crudo en BigQuery. Para WhatsApp usar `contact_hash`.

### `whatsapp_crm_contacts`

Fuente: `backend/schema_whatsapp_agent.sql`, `_save_whatsapp_contact_event`.

Uso:
- eventos bronze de contacto WhatsApp Cloud API;
- funnel por contacto pseudonimizado;
- fuente para silver/gold comercial.

Campos:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `event_id` | STRING | Evento unico |
| `contact_hash` | STRING | SHA-256 del telefono, sin telefono crudo |
| `display_name` | STRING | Nombre de perfil si Meta lo entrega |
| `channel` | STRING | `whatsapp` |
| `funnel_stage` | STRING | `interest`, `intent`, etc. |
| `intent` | STRING | Intencion detectada |
| `event_at` | TIMESTAMP | Fecha evento |
| `environment` | STRING | dev/qa/prod |

Vistas:
- `whatsapp_crm_contacts_silver`;
- `whatsapp_funnel_gold`.

Particion:
- `DAY` por `event_at`.

Clustering:
- `contact_hash`, `funnel_stage`, `intent`.

Relacion con `sales_opportunities`:
- esta tabla queda como bronze de touchpoints WhatsApp;
- `sales_opportunities` representa la oportunidad comercial consolidada.

### `payment_events`

Fuente: `_record_payment_event`.

Uso:
- auditoria de PayPal;
- ordenes creadas, capturas, errores, webhooks.

Campos esperados por codigo:
- `id`;
- `event_type`;
- `created_at`;
- `payload` como JSON serializado.

Accion recomendada:
- documentar/crear DDL formal en Terraform o SQL.

### `student_enrollments`

Fuente: `_record_student_enrollment`, `_mark_student_paid`.

Uso:
- alumnos o clientes de productos educativos pagados;
- estado de pago/acceso.

Campos escritos por codigo:
- `id`;
- `product_id`;
- `full_name`;
- `email`;
- `phone`;
- `country`;
- `role`;
- `company`;
- `message`;
- `source_page`;
- `signup_status`;
- `payment_status`;
- `payment_reference`;
- `access_status`;
- `created_at`.

Accion recomendada:
- crear DDL formal. Hoy se escribe desde codigo, pero no aparece completo en los
  esquemas revisados.

### `arco_requests`

Fuente: `backend/schema_arco.sql`, endpoint ARCO.

Uso:
- solicitudes de derechos ARCO Ley 21.719.

Campos principales:
- `arco_id`, `timestamp`;
- `tipo_derecho`;
- `nombre`, `run`, `email`;
- `detalle`;
- `estado`;
- `respuesta_timestamp`;
- `ip_address`, `user_agent`, `origin`;
- `notas_internas`;
- `created_at`, `updated_at`.

Vistas:
- `arco_statistics`;
- `arco_compliance`.

Riesgo actual:
- contiene PII sensible (`RUN`, email, detalle). Debe tener controles de acceso
  mas restrictivos que tablas de analitica comercial.

## Firestore

### Coleccion `revenue_access`

Fuente: `_activate_access`.

Uso:
- tokens de acceso a productos pagados;
- validacion de compra sin depender solo de email.

Documento:

| Campo | Descripcion |
| --- | --- |
| `email` | Email normalizado comprador |
| `product_id` | Producto comprado |
| `course_id` | Curso relacionado si aplica |
| `payment_status` | `COMPLETED` |
| `access_status` | `ACTIVE` |
| `provider_order_id` | Order ID PayPal |
| `provider_capture_id` | Capture ID PayPal |
| `activated_at` | Fecha activacion |

Clave de documento:
- token aleatorio `secrets.token_urlsafe(32)`.

### Coleccion `whatsapp_processed_messages`

Fuente: `_claim_whatsapp_message`.

Uso:
- idempotencia operacional para Meta WhatsApp Cloud API;
- evitar doble respuesta por retry o multi-instancia Cloud Run.

Documento:

| Campo | Descripcion |
| --- | --- |
| `message_id` | ID Meta |
| `contact_hash` | Hash del telefono |
| `environment` | dev/qa/prod |
| `created_at` | Timestamp servidor |

Clave de documento:
- `message_id`.

Accion recomendada:
- agregar TTL/retencion. Para idempotencia normalmente bastan 30 a 90 dias.

## PostgreSQL Local: `whatsapp-agent-local`

Fuente: `whatsapp-agent-local/schema.sql`.

Uso:
- agente 100% local en `agent01`;
- Baileys + Ollama + PostgreSQL;
- no depende de Meta Cloud API, Gemini ni GCP.

### `contacts`

Rol:
- dimension operacional de contacto WhatsApp local.

Campos:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `jid` | TEXT PK | JID de WhatsApp, por ejemplo `<phone>@s.whatsapp.net` |
| `phone` | TEXT | Telefono crudo |
| `display_name` | TEXT | Nombre visible |
| `push_name` | TEXT | Nombre push de WhatsApp |
| `first_seen` | TIMESTAMPTZ | Primer contacto |
| `last_seen` | TIMESTAMPTZ | Ultimo contacto |
| `intent` | TEXT | Ultima intencion conocida |
| `hot_lead` | BOOLEAN | Lead caliente |
| `human_handoff` | BOOLEAN | Bot pausado por derivacion humana |
| `message_count` | INTEGER | Conteo de mensajes recibidos |
| `notes` | TEXT | Notas operacionales |

Riesgo:
- almacena telefono crudo localmente. Esta bien para operacion local si el host
  esta protegido, pero no debe sincronizarse tal cual a BigQuery ni Git.

Recomendacion:
- agregar `contact_hash` y usarlo para exportaciones/sync.

### `messages`

Rol:
- fact table de mensajes locales.

Campos:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `chat_jid` | TEXT | Contacto/conversacion |
| `msg_id` | TEXT | ID mensaje WhatsApp |
| `direction` | TEXT | `in` o `out` |
| `sender` | TEXT | Remitente |
| `body` | TEXT | Texto |
| `intent` | TEXT | Intencion detectada |
| `model` | TEXT | Modelo usado |
| `latency_ms` | INTEGER | Latencia respuesta |
| `created_at` | TIMESTAMPTZ | Fecha mensaje |

Clave primaria:
- `(chat_jid, msg_id)`.

Indice:
- `(chat_jid, created_at DESC)`.

Fortaleza:
- deduplicacion local simple y correcta por chat/mensaje.

Limitacion:
- falta `provider`, `reply_to_msg_id`, `error`, `tokens`, `source`.

### `events`

Rol:
- event log flexible para cambios de estado y senales.

Campos:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `id` | BIGSERIAL PK | ID evento |
| `kind` | TEXT | Tipo evento |
| `chat_jid` | TEXT | Conversacion relacionada |
| `detail` | JSONB | Payload flexible |
| `created_at` | TIMESTAMPTZ | Fecha evento |

Indice:
- `(kind, created_at DESC)`.

Eventos esperados:
- `hot_lead_detected`;
- `human_handoff_requested`;
- `bot_resumed`;
- `ollama_timeout`;
- `message_ignored`;
- `reply_sent`.

### Modelo local recomendado para siguiente iteracion

Implementado en `whatsapp-agent-local/schema.sql`, sin romper lo existente:

```sql
ALTER TABLE contacts
  ADD COLUMN IF NOT EXISTS contact_hash TEXT,
  ADD COLUMN IF NOT EXISTS lead_score INTEGER,
  ADD COLUMN IF NOT EXISTS funnel_stage TEXT,
  ADD COLUMN IF NOT EXISTS next_action TEXT,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

CREATE UNIQUE INDEX IF NOT EXISTS contacts_contact_hash_idx
  ON contacts (contact_hash)
  WHERE contact_hash IS NOT NULL;

CREATE TABLE IF NOT EXISTS opportunities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_jid TEXT NOT NULL REFERENCES contacts(jid),
  contact_hash TEXT,
  service_key TEXT,
  stage TEXT NOT NULL DEFAULT 'new',
  lead_score INTEGER,
  estimated_min_usd INTEGER,
  estimated_max_usd INTEGER,
  currency TEXT DEFAULT 'USD',
  pain_point TEXT,
  urgency TEXT,
  next_action TEXT,
  owner TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS opportunities_stage_created_idx
  ON opportunities (stage, created_at DESC);
```

Notas:
- `gen_random_uuid()` requiere extension `pgcrypto`.
- El telefono crudo se queda local. Para cloud se exporta `contact_hash`.
- La vista local `sales_pipeline` resume oportunidades por etapa y servicio.

### `worker_jobs`

Rol:
- cola local de trabajo para agentes backoffice, inicialmente `agent02`;
- desacopla el agente WhatsApp en tiempo real de tareas mas pesadas como
  propuestas, SOW, briefs comerciales, investigacion de cuenta y seguimiento;
- evita que el bot envie documentos legales o comerciales sin aprobacion.

Campos:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `id` | UUID PK | ID del trabajo |
| `agent_name` | TEXT | Worker esperado, por ejemplo `agent02` |
| `job_type` | TEXT | `draft_proposal`, `draft_sow`, `draft_email`, `research_account`, `human_followup` |
| `status` | TEXT | `pending`, `claimed`, `done`, `failed`, `cancelled` |
| `priority` | INTEGER | Prioridad 0-100 |
| `opportunity_id` | UUID | Oportunidad asociada |
| `contact_jid` | TEXT | Contacto local asociado |
| `payload` | JSONB | Contexto flexible para el worker |
| `result` | JSONB | Resultado estructurado |
| `error` | TEXT | Error si falla |
| `claimed_by` | TEXT | Worker que tomo el trabajo |
| `claimed_at` | TIMESTAMPTZ | Fecha de toma |
| `due_at` | TIMESTAMPTZ | Plazo esperado |
| `created_at`, `updated_at` | TIMESTAMPTZ | Auditoria |

Indice principal:
- `(status, priority DESC, created_at ASC)`.

Regla operacional:
- `agent01` atiende WhatsApp y crea/actualiza oportunidades;
- `agent02` consume `worker_jobs`, genera artefactos y los deja para revision;
- ningun worker debe enviar contratos ni propuestas finales sin aprobacion humana.

### `sales_drafts`

Rol:
- repositorio local de borradores comerciales generados por agentes;
- sirve para propuestas, SOW, emails de seguimiento y briefs contractuales;
- mantiene supuestos y campos faltantes visibles antes de enviar al cliente.

Campos:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `id` | UUID PK | ID del borrador |
| `opportunity_id` | UUID | Oportunidad relacionada |
| `contact_jid` | TEXT | Contacto local relacionado |
| `draft_type` | TEXT | `proposal`, `sow`, `followup_email`, `contract_brief` |
| `status` | TEXT | `draft`, `ready_for_review`, `approved`, `sent`, `archived` |
| `title` | TEXT | Titulo legible |
| `body` | TEXT | Contenido del borrador |
| `assumptions` | JSONB | Supuestos que requieren revision |
| `missing_fields` | JSONB | Datos faltantes antes de enviar |
| `created_by` | TEXT | Agente creador |
| `reviewed_by`, `reviewed_at` | TEXT/TIMESTAMPTZ | Revision humana |
| `sent_at` | TIMESTAMPTZ | Envio posterior a aprobacion |
| `metadata` | JSONB | Trazabilidad flexible |
| `created_at`, `updated_at` | TIMESTAMPTZ | Auditoria |

Regla de venta:
- los borradores pueden ser rapidos y agenticos;
- el estado `approved` debe representar una accion humana o un flujo de
  aprobacion explicito;
- `sent` solo debe marcarse despues de un envio real y auditable.

## PostgreSQL Master Program

Fuente: `aif369-agents/db/schema.sql`.

Dominio:
- programas, meses, modulos;
- lecciones, labs, evaluaciones;
- cohorts, students;
- progreso y notas;
- capstone;
- fuentes legales;
- revisiones de contenido.

Tablas principales:
- `programs`;
- `months`;
- `modules`;
- `lessons`;
- `labs`;
- `assessments`;
- `cohorts`;
- `students`;
- `student_lessons`;
- `student_labs`;
- `student_assessments`;
- `capstones`;
- `capstone_artifacts`;
- `legal_sources`;
- `content_reviews`.

Observacion:
- Este modelo es independiente del CRM/WhatsApp. Debe integrarse con ventas solo
  mediante `student_enrollments`, productos o un futuro `customer_id`.

## Flujo de Datos Comercial Recomendado

### WhatsApp Cloud API

```text
Meta webhook
  -> Firestore whatsapp_processed_messages
  -> chat_conversations
  -> whatsapp_crm_contacts
  -> alerta email si hot lead
  -> crm_agent_quotes si pide cotizacion
```

### WhatsApp Local

```text
Baileys
  -> PostgreSQL local contacts/messages/events
  -> agente Ollama
  -> events hot_lead/handoff
  -> export opcional anonimizado a BigQuery
```

### Web Chat

```text
chat-widget.js
  -> /api/chat
  -> chat_conversations
  -> chat_session_metadata
  -> crm_agent_quotes si cotiza
```

### Forms / Scorecard

```text
formularios web
  -> contact_form_submissions
  -> scorecard_submissions
  -> email alerta
  -> futuro: sales_opportunities
```

## Brechas Prioritarias

1. **Poblar el contrato unico de leads.** `sales_opportunities` ya tiene DDL; falta
   escribir oportunidades desde formularios, chat, scorecard, WhatsApp y pagos.

2. **Alinear schemas con codigo.** `chat_conversations` escribe mas campos que
   los definidos en Terraform.

3. **Parametrizar SQL.** `schema_crm_agent.sql`, `schema_arco.sql` y
   `schema_metadata.sql` usan project/dataset productivo literal.

4. **PII y privacidad.** WhatsApp local guarda telefono crudo. Debe quedarse
   local y exportar solo hash.

5. **Retencion.** Definir retencion para mensajes, eventos, ARCO y claims de
   idempotencia.

6. **MCP/A2A.** Antes de sumar herramientas, registrar cada accion externa con
   `trace_id`, `agent_id`, `tool_name`, `input_hash`, `status`, `created_at`.

## Proxima Migracion Recomendada

Crear una migracion incremental para:

- aplicar `backend/schema_sales_opportunities.sql` en DEV/QA;
- escribir oportunidades desde backend;
- exportar oportunidades anonimizadas desde `whatsapp-agent-local`;
- crear `agent_action_events` en BigQuery;
- crear jobs de reconciliacion entre `crm_agent_quotes`,
  `whatsapp_crm_contacts`, `chat_conversations` y `sales_opportunities`.
