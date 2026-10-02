# AIF369 Agentic Sales Sprints

## Objetivo

Convertir los canales actuales de AIF369 en un equipo agentico comercial capaz
de atender WhatsApp, web chat y email; calificar leads; generar propuestas;
coordinar follow-up; y escalar a humano cuando exista intención real de compra.

La ruta de promoción respeta la política del repositorio:

```text
feature/local -> dev -> qa -> PR qa-to-main -> aprobación humana -> producción
```

## Principios

- Vender primero, sofisticar después.
- No almacenar teléfonos, tokens, credenciales ni logs crudos en Git.
- WhatsApp y email deben registrar trazabilidad comercial sin exponer datos
  sensibles innecesarios.
- Todo agente que ejecute acciones externas debe usar herramientas auditables.
- Producción queda bloqueada hasta PR aprobado por el owner humano.

## Sprint 1: WhatsApp Sales Agent Operativo

### Objetivo

Lograr que AIF369 pueda recibir, responder y auditar mensajes reales por
WhatsApp en DEV/QA, con foco en primeras oportunidades comerciales.

### Entregables

- Webhook WhatsApp validado con firma Meta.
- Secrets `WHATSAPP_*` vinculados en DEV y QA.
- Deduplicación persistente de `message_id` para evitar doble respuesta.
- Memoria mínima de conversación por `session_id`.
- Registro de conversación en `chat_conversations`.
- Registro CRM en `whatsapp_crm_contacts`.
- Alerta por email para leads calientes.
- Script o checklist de validación DEV/QA.

### Criterios de aceptación

- Challenge `GET /api/whatsapp/webhook` responde con token correcto.
- Firma inválida retorna `401`.
- Mensaje de texto genera una sola respuesta.
- Retry del mismo `message_id` no vuelve a enviar WhatsApp.
- Lead con intención de cotizar/agendar dispara alerta por email.
- BigQuery contiene conversación y evento CRM sin teléfono crudo.

## Sprint 2: Equipo Agentico Comercial

### Objetivo

Separar responsabilidades comerciales en agentes coordinados.

### Agentes

- `Sales Intake Agent`: recibe WhatsApp, web chat y futuros emails.
- `Qualifier Agent`: detecta rol, empresa, dolor, urgencia y presupuesto.
- `Proposal Agent`: arma rango de propuesta y siguiente paso.
- `Follow-up Agent`: prepara seguimiento por email o WhatsApp.
- `Handoff Agent`: escala a humano con resumen accionable.
- `CRM Memory Agent`: consolida estado del lead y oportunidad.

### Orquestación

- LangGraph para el flujo de conversación y estados comerciales.
- Eventos internos compatibles con un contrato A2A simple:
  `source_agent`, `target_agent`, `event_type`, `lead_id`, `payload`,
  `created_at`, `trace_id`.
- Herramientas MCP para acciones externas donde aplique: email, calendario,
  documentos, CRM o storage.

### Criterios de aceptación

- Un mensaje entrante produce un estado comercial explícito.
- El orquestador decide responder, cotizar, pedir dato faltante o escalar.
- Cada agente deja evidencia mínima de entrada/salida.
- Ningún agente ejecuta email/calendario sin herramienta auditada.

## Sprint 3: Omnicanal y Follow-up

### Objetivo

Conectar ventas por WhatsApp con email, calendario y propuesta comercial.

### Entregables

- Plantillas de email: lead nuevo, seguimiento, propuesta, agendamiento.
- Envío de email vía herramienta auditada.
- Integración de calendario para proponer o crear reuniones.
- Resumen ejecutivo del lead antes de handoff humano.
- Vista de pipeline simple por etapa e intención.

### Criterios de aceptación

- Lead caliente recibe siguiente paso claro.
- El humano recibe contexto suficiente para cerrar sin releer toda la conversación.
- El sistema distingue respuesta automática, propuesta y derivación humana.

## Sprint 4: Plataforma Agentica Gobernada

### Objetivo

Convertir la solución en una plataforma reutilizable para AIF369 y clientes.

### Entregables

- Registro de agentes, tools y permisos.
- Auditoría de decisiones y acciones.
- Métricas de conversión por canal.
- Guardrails de compliance y privacidad.
- Playbooks comerciales por servicio.
- Checklist de promoción DEV -> QA -> producción.

### Criterios de aceptación

- Cada acción externa queda vinculada a `trace_id`.
- Cada lead puede reconstruirse sin exponer secretos ni teléfonos crudos.
- QA tiene evidencia completa antes de abrir PR productivo.

## Backlog Técnico Inicial

- Parametrizar aplicación SQL por ambiente sin edición manual.
- Crear tabla o colección de oportunidades comerciales.
- Agregar `lead_score`, `funnel_stage` y `next_action`.
- Consolidar backend WhatsApp con `aif369-agents`.
- Evaluar LangGraph como runtime del flujo comercial.
- Definir contratos MCP/A2A internos antes de agregar más herramientas.
- Agregar smoke tests contra DEV para WhatsApp y health checks.
