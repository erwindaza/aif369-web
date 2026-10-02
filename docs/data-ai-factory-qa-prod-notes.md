# Data & AI Factory - QA/PROD Notes

## Pendientes Para QA

- Validar render responsive en mobile, tablet y desktop.
- Validar que `/data-ai-factory` resuelva correctamente en Vercel con `cleanUrls`.
- Enviar formulario desde ambiente DEV y confirmar recepcion en backend DEV/BigQuery/email.
- Revisar copy comercial con owner antes de promocionar a QA.
- Confirmar si se agregaran precios, duraciones o SLAs por paquete.

## Evidencia Recomendada Antes De PROD

- Link de workflow DEV exitoso.
- Link de workflow QA exitoso.
- Screenshot de home con seccion `Data & AI Factory`.
- Screenshot de `/data-ai-factory`.
- Resultado de prueba del formulario sin exponer datos sensibles.
- Revision SEO basica: title, description, canonical y sitemap.

## Impacto Productivo

- Cambio comercial visible en home, menu, footer y sitemap.
- Nueva pagina publica para captacion de leads.
- No introduce secretos ni nuevas dependencias.
- No modifica backend ni infraestructura.

## Rollback

- Revertir los cambios en `index.html`, `sitemap.xml` y eliminar `data-ai-factory.html`.
- Eliminar o dejar archivados los documentos en `docs/` segun criterio del owner.

