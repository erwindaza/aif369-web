# Especificacion DEV - Data & AI Factory

## Objetivo

Integrar en `www.aif369.com` una nueva linea de producto llamada **Data & AI Factory**, orientada a vender servicios concretos de datos e IA para empresas en Chile y LATAM.

## Alcance Implementado

- Seccion visible en la home con titulo `Data & AI Factory`.
- Pagina dedicada disponible como `data-ai-factory.html`; en Vercel tambien queda accesible como `/data-ai-factory` por `cleanUrls`.
- Acceso desde el menu principal de la home y desde el footer.
- Paquetes comerciales:
  - Data Sprint.
  - Dashboard Ejecutivo.
  - AI Enrichment Pipeline.
  - Data Factory Cell.
- Casos de uso concretos:
  - Reportes manuales en Excel.
  - Integracion desde APIs, archivos, bases de datos y cloud.
  - Pipelines ETL/ELT batch o near real time.
  - Dashboards comerciales, financieros, operacionales y de marketing.
  - Enriquecimiento de catalogos con IA.
  - Clasificacion automatica de registros.
- Stack tecnologico y metodo de trabajo.
- CTA de contacto y formulario conectado al endpoint existente `/api/contact`.

## Formulario

El formulario usa `data-contact-form` y `data-endpoint="/api/contact"`, por lo que reutiliza la logica existente de `scripts.js`.

En ambiente no productivo, `scripts.js` selecciona el backend DEV:

`https://aif369-backend-api-dev-es7l2buwdq-uc.a.run.app`

Campos enviados:

- `fullName`
- `email`
- `company`
- `role`
- `interest`
- `context`
- `form_type=data-ai-factory`

## Archivos Modificados

- `index.html`: menu, seccion comercial en home y footer.
- `data-ai-factory.html`: nueva pagina dedicada.
- `sitemap.xml`: nueva URL comercial.
- `docs/data-ai-factory-dev-spec.md`: especificacion DEV.
- `docs/data-ai-factory-qa-prod-notes.md`: pendientes QA/PROD.

