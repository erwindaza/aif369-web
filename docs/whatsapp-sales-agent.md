# Agente comercial de WhatsApp

## Alcance

El backend expone `GET/POST /api/whatsapp/webhook` para la API oficial de Meta
WhatsApp Cloud. Verifica la firma del webhook, responde consultas comerciales,
genera cotizaciones orientativas con el mismo motor CRM del chat web y registra
la conversación en BigQuery.

Los teléfonos no se persisten: se usa un hash SHA-256 estable como identificador
del contacto. Los eventos CRM alimentan las capas bronze, silver y gold definidas
en `backend/schema_whatsapp_agent.sql`.

## Configuración por ambiente

Crear los siguientes valores en Secret Manager y vincularlos al servicio Cloud
Run correspondiente. Nunca guardarlos en Git ni imprimirlos en logs:

- `WHATSAPP_VERIFY_TOKEN`: token elegido para verificar el webhook.
- `WHATSAPP_ACCESS_TOKEN`: token de sistema de Meta con permiso de mensajería.
- `WHATSAPP_PHONE_NUMBER_ID`: identificador del número emisor.
- `WHATSAPP_APP_SECRET`: secreto de la aplicación para validar firmas.
- `WHATSAPP_GRAPH_VERSION` (opcional): versión de Graph API; por defecto `v23.0`.

Los workflows de backend ya esperan estos nombres de Secret Manager:

| Ambiente | Secret Manager |
| --- | --- |
| DEV | `aif369-whatsapp-verify-token-dev`, `aif369-whatsapp-access-token-dev`, `aif369-whatsapp-phone-number-id-dev`, `aif369-whatsapp-app-secret-dev` |
| QA | `aif369-whatsapp-verify-token-qa`, `aif369-whatsapp-access-token-qa`, `aif369-whatsapp-phone-number-id-qa`, `aif369-whatsapp-app-secret-qa` |

En Meta Developers, configurar como callback:

`https://<backend-del-ambiente>/api/whatsapp/webhook`

Suscribir el campo `messages`. Ejecutar el SQL del ambiente reemplazando proyecto
y dataset antes de activar tráfico. En DEV y QA se deben usar datasets y números
de prueba separados de producción.

Ejemplo DEV:

```bash
sed -e 's/__PROJECT_ID__/aif369-backend/g' \
  -e 's/__DATASET_ID__/aif369_analytics_dev/g' \
  backend/schema_whatsapp_agent.sql | bq query --use_legacy_sql=false
```

Ejemplo QA:

```bash
sed -e 's/__PROJECT_ID__/aif369-backend/g' \
  -e 's/__DATASET_ID__/aif369_analytics_qa/g' \
  backend/schema_whatsapp_agent.sql | bq query --use_legacy_sql=false
```

## Validación QA

1. Completar el challenge GET con un token correcto y rechazar uno incorrecto.
2. Confirmar que un payload con firma inválida retorna HTTP 401.
3. Enviar un mensaje de texto desde el número de prueba y verificar una respuesta.
4. Pedir una cotización y comprobar `provider=crm_quote_agent` en BigQuery.
5. Reenviar el mismo `message_id` y comprobar que no se envía una segunda respuesta.
6. Confirmar eventos en bronze y resultados de las vistas silver/gold.
