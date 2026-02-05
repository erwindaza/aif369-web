# Configuración de Email Corporativo edaza@aif369.com

## Opciones para crear email @aif369.com

### Opción 1: Google Workspace (Recomendado)
**Costo:** ~$6 USD/mes por usuario

1. **Registrar dominio en Google Domains o usar registrar actual**
   - Ir a [workspace.google.com](https://workspace.google.com)
   - Crear cuenta empresarial para aif369.com

2. **Verificar dominio**
   - Agregar registro TXT en DNS del dominio
   - Esperar verificación (puede tardar hasta 72 horas)

3. **Configurar registros MX**
   ```
   Prioridad  Servidor
   1          ASPMX.L.GOOGLE.COM
   5          ALT1.ASPMX.L.GOOGLE.COM
   5          ALT2.ASPMX.L.GOOGLE.COM
   10         ALT3.ASPMX.L.GOOGLE.COM
   10         ALT4.ASPMX.L.GOOGLE.COM
   ```

4. **Crear usuario edaza@aif369.com**
   - Ir a Admin Console
   - Usuarios → Agregar usuario
   - Email: edaza@aif369.com

5. **Acceder a Gmail**
   - mail.google.com o gmail.com
   - Iniciar sesión con edaza@aif369.com

**Ventajas:**
- ✅ Integración con Gmail, Calendar, Drive, Meet
- ✅ 30GB almacenamiento por usuario
- ✅ Gestión avanzada de usuarios
- ✅ Soporte 24/7

---

### Opción 2: Zoho Mail (Alternativa económica)
**Costo:** Gratis hasta 5 usuarios, luego $1/mes

1. Ir a [zoho.com/mail](https://www.zoho.com/mail/)
2. Registrar dominio aif369.com
3. Verificar dominio con registro TXT
4. Configurar registros MX de Zoho
5. Crear buzón edaza@aif369.com

---

### Opción 3: Email con SendGrid + Cloud Functions (Para envíos automáticos)

Si solo necesitas **enviar** emails automáticos (no recibir), puedes usar SendGrid:

```python
# backend/send_email.py
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_contact_notification(contact_data):
    message = Mail(
        from_email='noreply@aif369.com',
        to_emails='erwin.daza@gmail.com',  # tu email personal
        subject=f'Nuevo contacto de {contact_data["name"]}',
        html_content=f'''
        <h2>Nuevo mensaje de contacto</h2>
        <p><strong>Nombre:</strong> {contact_data["name"]}</p>
        <p><strong>Email:</strong> {contact_data["email"]}</p>
        <p><strong>Empresa:</strong> {contact_data.get("company", "N/A")}</p>
        <p><strong>Mensaje:</strong></p>
        <p>{contact_data["message"]}</p>
        '''
    )
    
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        return response.status_code
    except Exception as e:
        print(f"Error sending email: {e}")
        return None
```

**Configuración SendGrid:**
1. Crear cuenta en [sendgrid.com](https://sendgrid.com)
2. Verificar dominio aif369.com
3. Configurar DNS records (SPF, DKIM, etc.)
4. Obtener API Key
5. Plan gratuito: 100 emails/día

---

## Recomendación para AIF369

Para un sitio corporativo profesional como AIF369:

**Google Workspace** es la mejor opción porque:
- Email profesional completo (enviar y recibir)
- Integración con herramientas de productividad
- Buena reputación de dominio (evita spam)
- Fácil gestión de múltiples usuarios si creces

**Configuración paso a paso:**

```bash
# 1. Comprar Google Workspace
# Ir a: https://workspace.google.com/
# Seguir wizard para aif369.com

# 2. Una vez verificado el dominio, configurar MX records en tu proveedor DNS
# (GoDaddy, Cloudflare, Namecheap, etc.)

# 3. Esperar propagación DNS (1-48 horas)

# 4. Acceder a https://admin.google.com
# - Crear usuario: edaza
# - Dominio: aif369.com
# - Email resultante: edaza@aif369.com

# 5. Acceder a Gmail
# https://mail.google.com
# Usuario: edaza@aif369.com
```

## Integración con el formulario

Una vez configurado el email, puedes:

1. **Recibir notificaciones** cuando alguien envíe el formulario
2. **Responder directamente** desde edaza@aif369.com
3. **Configurar respuesta automática** al usuario

Actualiza el backend para enviar emails:

```python
# Agregar a backend/requirements.txt
sendgrid==6.11.0

# Agregar notificación en backend/main.py después de guardar en BigQuery
from send_email import send_contact_notification
send_contact_notification(row)
```

## Costos estimados

| Opción | Costo mensual | Usuarios | Funciones |
|--------|---------------|----------|-----------|
| Google Workspace | $6 | 1 | Email + Suite completa |
| Zoho Mail | Gratis | Hasta 5 | Solo email |
| SendGrid | Gratis | N/A | Solo envío (100/día) |

---

**¿Qué opción prefieres? Te ayudo con la configuración que elijas.**
