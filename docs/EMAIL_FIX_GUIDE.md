# Guía para Activar Notificaciones por Email - AIF369

## Problema
Los emails no están siendo enviados porque falta configurar la contraseña SMTP en Cloud Run.

## Solución

### Paso 1: Crear contraseña de aplicación en Zoho Mail

1. **Iniciar sesión en Zoho Mail**
   - Ir a [mail.zoho.com](https://mail.zoho.com)
   - Entrar con `edaza@aif369.com`

2. **Generar contraseña de aplicación**
   - Ir a **Configuración** (icono engranaje arriba derecha)
   - Seleccionar **Seguridad**
   - Buscar **Contraseñas de aplicación**
   - Hacer clic en **Generar nueva contraseña**
   - Nombre: `AIF369 Backend Cloud Run`
   - Copiar la contraseña generada (solo se muestra una vez)

### Paso 2: Guardar contraseña en Secret Manager de GCP

```bash
# Crear el secret en Google Cloud Secret Manager
gcloud secrets create aif369-smtp-password \
  --project=aif369-backend \
  --replication-policy="automatic" \
  --data-file=- <<< "TU_CONTRASEÑA_AQUÍ"

# Verificar que se creó correctamente
gcloud secrets versions access latest \
  --secret=aif369-smtp-password \
  --project=aif369-backend
```

### Paso 3: Dar permisos al Service Account

```bash
# Otorgar permiso al Service Account para acceder al secret
gcloud secrets add-iam-policy-binding aif369-smtp-password \
  --project=aif369-backend \
  --member="serviceAccount:aif369-backend-sa@aif369-backend.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Paso 4: Redesplegar el servicio

```bash
cd /Users/macbookpro/dev/aif369-web

# Ejecutar el script de despliegue actualizado
./backend/deploy.sh
```

El script ahora incluye:
- ✅ Variable de entorno `SMTP_USER=edaza@aif369.com`
- ✅ Variable de entorno `NOTIFICATION_EMAIL=erwin.daza@gmail.com`
- ✅ Secret `SMTP_PASSWORD` desde Secret Manager

## Verificar funcionamiento

### 1. Ver logs del servicio

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=aif369-backend-api" \
  --project=aif369-backend \
  --limit=50 \
  --format=json
```

### 2. Probar envío de email

Ir al sitio web y enviar un formulario de contacto. Deberías ver:

**En los logs de Cloud Run:**
```
Email notification sent to erwin.daza@gmail.com
Confirmation email sent to [email-del-usuario]
```

**En tu email (erwin.daza@gmail.com):**
- Un email con el asunto "Nuevo contacto: [Nombre]"
- Contenido del formulario

**El usuario recibirá:**
- Email con el asunto "✓ Hemos recibido tu solicitud - AIF369"
- Confirmación de su envío

## Troubleshooting

### Error: "SMTP authentication failed"

**Causa:** Contraseña incorrecta o no generada como "contraseña de aplicación"

**Solución:**
1. Volver a Zoho Mail
2. Generar nueva contraseña de aplicación
3. Actualizar el secret:
   ```bash
   echo -n "NUEVA_CONTRASEÑA" | gcloud secrets versions add aif369-smtp-password --data-file=-
   ```
4. Redesplegar con `./backend/deploy.sh`

### Error: "Permission denied on secret"

**Causa:** Service Account sin permisos

**Solución:**
```bash
gcloud secrets add-iam-policy-binding aif369-smtp-password \
  --project=aif369-backend \
  --member="serviceAccount:aif369-backend-sa@aif369-backend.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Los emails no llegan a Gmail (erwin.daza@gmail.com)

**Posibles causas:**
1. Email en carpeta de spam
2. Bloqueado por Gmail

**Solución:**
- Revisar carpeta de spam en Gmail
- Marcar como "No es spam" si aparece ahí
- Agregar `edaza@aif369.com` a contactos

### Verificar configuración actual del servicio

```bash
gcloud run services describe aif369-backend-api \
  --region=us-central1 \
  --project=aif369-backend \
  --format="yaml(spec.template.spec.containers[0].env)"
```

## Arquitectura de Emails

```
Usuario llena formulario
         ↓
Backend API recibe POST /api/contact
         ↓
1. Guarda en BigQuery ✅
         ↓
2. Envía email a erwin.daza@gmail.com (notificación)
   - Servidor: smtp.zoho.com:587
   - De: edaza@aif369.com
   - A: erwin.daza@gmail.com
         ↓
3. Envía email al usuario (confirmación)
   - De: edaza@aif369.com
   - A: email del usuario
```

## Checklist Final

- [ ] Contraseña de aplicación creada en Zoho Mail
- [ ] Secret `aif369-smtp-password` creado en Secret Manager
- [ ] Service Account con permisos `secretmanager.secretAccessor`
- [ ] Script `deploy.sh` actualizado con variables de entorno
- [ ] Backend redesplegado con `./backend/deploy.sh`
- [ ] Prueba de formulario enviada desde el sitio web
- [ ] Email recibido en erwin.daza@gmail.com
- [ ] Email de confirmación recibido por el usuario de prueba

## Comandos rápidos

```bash
# Ver URL del servicio
gcloud run services describe aif369-backend-api \
  --region=us-central1 \
  --project=aif369-backend \
  --format='value(status.url)'

# Ver logs en tiempo real
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=aif369-backend-api" \
  --project=aif369-backend

# Test manual del endpoint
curl -X POST https://aif369-backend-api-830685315001.us-central1.run.app/api/contact \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Usuario",
    "email": "test@example.com",
    "company": "Test Company",
    "message": "Este es un mensaje de prueba"
  }'
```
