# AIF369 DEV GUIDE

## Objetivo
Documento vivo para registrar avances, decisiones y despliegues en **DEV**. No publicar en PROD sin aprobación explícita.

## Estado actual (DEV)
- Frontend desplegado en Vercel (rama `dev`).
- Backend desplegado en Cloud Run (servicio `aif369-backend-api`).
- Formularios: `index.html` -> `/api/contact`, `education.html` -> `/api/education` (con fallback a prod mientras se levanta backend dev).

## Fases

### Fase 1: Formulario de contacto
- Objetivo: enviar datos a backend y emails.
- Estado: **completado** en DEV.

### Fase 2: Formulario de educación
- Objetivo: enviar datos a `/api/education`.
- Estado: **completado** en DEV.
- Nota: añadir backend **dev** dedicado cuando esté listo.

### Fase 3: Multilenguaje
- Objetivo: toggle ES/EN funcionando.
- Estado: **completado** en DEV.

### Fase 4: Servicios MLOps/LLMOps
- Objetivo: sección con texto y CTA.
- Estado: **completado** en DEV.

### Fase 5: Página Autor
- Objetivo: nueva página sobre el autor y link en navegación.
- Estado: **completado** en DEV.
- Pendiente: validar contenido final (bio/foto/logos).

### Fase 6: Branding
- Objetivo: integrar logo oficial (header/footer/favicon).
- Estado: **pendiente** (falta archivo final con fondo transparente).

## Despliegues (DEV)
- Cloud Run: `aif369-backend-api` (us-central1)
- Vercel: rama `dev`

## Pendientes críticos
- Definir si habrá backend **dev** separado (`aif369-backend-api-dev`).
- Definir estrategia para versión móvil separada (web mobile vs app Android Java).
- Entregar logo oficial en PNG/SVG con fondo transparente.

## Validaciones
Checklist antes de pasar a PROD:
- [ ] Formularios envían email y guardan en BigQuery.
- [ ] Toggle ES/EN en todas las páginas.
- [ ] Navegación correcta en header y footer.
- [ ] Revisión visual en desktop y mobile.
- [ ] Logo oficial integrado en header/footer/favicon.
