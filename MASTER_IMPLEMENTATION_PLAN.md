# AIF369 Master Implementation Plan

## Overview

Implementar el **AIF369 Master en Arquitectura, Gobernanza de Datos e Inteligencia Artificial** usando:
- **6 agentes especializados** que "dictan" el Master
- **Landing + malla curricular** en aif369.com
- **Módulos, laboratorios, evaluaciones, capstone** con contenido validado
- **Panel de administración** para docentes y administradores

**Base**: `aif369_master_data_ai_governance.json` (especificación completa)

---

## Phase 1: Foundation (Weeks 1-2)

### 1.1 Agentes Especializados

#### A. **Instructor Agent** (Llama 70B)
- **Rol**: Dicta módulos, explica conceptos, proporciona ejemplos
- **Responsabilidad**: Generar contenido de lecciones paso a paso
- **Entrada**: Título módulo, tema, objetivo de aprendizaje
- **Salida**: Estructura lesson JSON + contenido educativo
- **Constraints**: Parafrasear estándares, no copiar ISO/TOGAF/DAMA protegidos

#### B. **Evaluator Agent** (Mistral 7B)
- **Rol**: Evalúa entregables, laboratorios, case studies
- **Responsabilidad**: Rúbricas, criterios de aceptación, feedback automático
- **Entrada**: Entregable del estudiante, rúbrica, respuesta esperada
- **Salida**: Puntuación, feedback, areas de mejora

#### C. **RAG Tutor Agent** (Llama + Vector DB)
- **Rol**: Responde preguntas sobre curriculum, normas, architecture
- **Responsabilidad**: Citación de fuentes, verificación de respuestas
- **Entrada**: Pregunta del estudiante sobre Master
- **Salida**: Respuesta con citas de documentos aprobados
- **Sources**: Referencias legal, TOGAF, DAMA, ISO, cloud docs versionadas

#### D. **Lab Guide Agent** (Mistral 7B)
- **Rol**: Guía laboratorios prácticos, debugging, troubleshooting
- **Responsabilidad**: Instrucciones paso a paso, validación de ejercicios
- **Entrada**: Lab ID, paso actual, problema del estudiante
- **Salida**: Pista, validación, siguiente paso
- **Tools**: Git, Docker, Cloud CLI, diagramming tools

#### E. **Capstone Supervisor Agent** (Claude/Llama)
- **Rol**: Supervisa proyecto integrador Retail LATAM Agentic
- **Responsabilidad**: Revisar artifacts, architecture, trade-offs, presentación
- **Entrada**: Artefacto capstone (arquitectura, código, DPIA, etc.)
- **Salida**: Feedback técnico, legal, cumplimiento de criterios
- **Validation**: 20+ artifacts mandatorios, acceptance criteria

#### F. **Compliance Agent** (Claude)
- **Rol**: Asegura cumplimiento legal, regulatorio, ético
- **Responsabilidad**: Review de contenido antes de publicación
- **Entrada**: Contenido (lección, lab, capstone artifact)
- **Salida**: ✓ Aprobado | ⚠️ Requiere revisión legal | ❌ Rechazado
- **Checks**: 
  - ¿Afirma falsamente acreditación oficial?
  - ¿Copia texto protegido de ISO?
  - ¿Cita fuentes en contenido legal?
  - ¿Usa disclaimer en "Master" comercial?

### 1.2 Backend API (FastAPI)

**Endpoints principales**:

```bash
# Content Management
POST   /api/master/lessons        # Crear lección (Instructor Agent)
PUT    /api/master/lessons/{id}   # Actualizar con validación
GET    /api/master/curriculum     # Malla curricular
GET    /api/master/month/{n}      # Detalle del mes N

# Learning
POST   /api/master/assess         # Enviar evaluación
POST   /api/master/lab/submit    # Enviar lab
GET    /api/master/tutor         # Consulta RAG Tutor

# Capstone
POST   /api/master/capstone       # Enviar artefacto
GET    /api/master/capstone/{id}  # Estado del capstone

# Admin
GET    /api/admin/content/review  # Cola de revisión
POST   /api/admin/publish         # Publicar contenido aprobado
GET    /api/admin/analytics       # Progreso de cohorte
```

---

## Phase 2: Content Structure (Weeks 3-4)

### 2.1 Database Schema

```sql
-- Program
CREATE TABLE programs (
  id TEXT PRIMARY KEY,
  official_name TEXT,
  slug TEXT UNIQUE,
  status ENUM('draft', 'published'),
  created_at TIMESTAMP
);

-- Curriculum
CREATE TABLE months (
  id TEXT PRIMARY KEY,
  program_id FKEY programs,
  month_number INT (1-12),
  title TEXT,
  created_at TIMESTAMP
);

CREATE TABLE modules (
  id TEXT PRIMARY KEY,
  month_id FKEY months,
  title TEXT,
  order INT,
  created_at TIMESTAMP
);

-- Content
CREATE TABLE lessons (
  id TEXT PRIMARY KEY,
  month_id FKEY months,
  module_id FKEY modules,
  title TEXT,
  status ENUM('draft', 'expert_review', 'legal_review', 'approved', 'published'),
  requires_legal_review BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP,
  reviewed_by TEXT,
  reviewed_at TIMESTAMP
);

CREATE TABLE labs (
  id TEXT PRIMARY KEY,
  month_id FKEY months,
  title TEXT,
  status ENUM(...),
  created_at TIMESTAMP
);

CREATE TABLE assessments (
  id TEXT PRIMARY KEY,
  month_id FKEY months,
  type ENUM('quiz', 'case_study', 'artifact_review'),
  status ENUM(...),
  created_at TIMESTAMP
);

-- Legal Sources (versionado)
CREATE TABLE legal_sources (
  id TEXT PRIMARY KEY,
  title TEXT,
  jurisdiction TEXT,
  source_type TEXT,
  url TEXT,
  effective_date DATE,
  version TEXT,
  valid_until DATE,
  created_at TIMESTAMP
);

-- Capstone
CREATE TABLE capstones (
  id TEXT PRIMARY KEY,
  student_id TEXT,
  status ENUM('in_progress', 'submitted', 'under_review', 'approved', 'failed'),
  created_at TIMESTAMP
);

CREATE TABLE capstone_artifacts (
  id TEXT PRIMARY KEY,
  capstone_id FKEY capstones,
  artifact_type TEXT (architecture, code, dpia, etc),
  status ENUM('pending', 'approved', 'needs_revision'),
  reviewed_by TEXT,
  feedback TEXT,
  created_at TIMESTAMP
);
```

### 2.2 Landing Page

- **URL**: `/master` or `/master-arquitectura-gobernanza-datos`
- **Sections**:
  1. Hero + CTA (Admisión, Descargar brochure)
  2. Disclaimer académico (importante - "Master comercial, no grado oficial")
  3. Descripción 12 meses, 420h
  4. Público objetivo + Perfil de egreso
  5. Malla curricular (preview)
  6. Capstone Retail LATAM (video, demo)
  7. Certificaciones relacionadas (sin afirmar acreditación oficial)
  8. Docentes y mentores
  9. FAQ
  10. Precios y admisión

### 2.3 Curriculum Page

- Tabla interactiva: 12 meses → módulos → learning outcomes
- Filtrar por:
  - Dominio (Enterprise Architecture, Data Governance, etc)
  - Certificación relacionada (TOGAF, ISO 27001, etc)
  - Palabra clave
- Descargar malla en PDF/Excel

---

## Phase 3: Instructor Agent Integration (Weeks 5-7)

### 3.1 Lesson Generation Workflow

```
Admin: "Crear lección - Mes 1, Módulo 'Enterprise Architecture fundamentals'"
  ↓
Instructor Agent:
  1. Load curriculum spec from JSON
  2. Generar estructura lesson (learning objectives, examples, activity)
  3. Escribir secciones (nunca copiar TOGAF - parafrasear + citar)
  4. Crear 2-3 ejemplos situados en Chile/LATAM
  5. Proponer knowledge check (5 preguntas)
  6. Output: lesson.json
  ↓
Compliance Agent:
  - ¿Cita TOGAF o afirma ser TOGAF oficial?
  - ¿Hay disclaimer de términos no protegidos?
  - ¿Ejemplos respetan privacidad?
  ↓
Expert Review (humano):
  - Arquitecto revisa contenido técnico
  - Especialista en TOGAF valida precisión
  ↓
Publicar en DB
```

### 3.2 Content Guardrails

**Prohibido**:
- Copiar texto completo de ISO, TOGAF, DAMA sin licencia
- Afirmar "Certificado oficial TOGAF" sin convenio
- Generar consejos legales automatizados

**Obligatorio**:
- Parafrasear + citar fuente oficial
- Usar ejemplos de casos reales (con privacidad respetada)
- Incluir at least 1 diagram (Mermaid/DrawIO), 1 lab, 1 case study

---

## Phase 4: RAG Tutor & Legal Sources (Weeks 8-9)

### 4.1 Vector Database Setup

```python
# Approved sources only
sources = [
  "ISO/IEC 27001:2022 official summary (paraphrased)",
  "NIST AI RMF documentation",
  "EU AI Act (official text)",
  "DAMA-DMBOK principles (official)",
  "TOGAF 9.2 Foundation concepts",
  "AWS/Azure/GCP official documentation",
  "Chilean data protection laws (official)",
  "AIF369 approved lesson content"
]

# Embed + index
embeddings = OpenAI(text-embedding-3-small)
vector_db.add(sources)
```

### 4.2 RAG Tutor Workflow

```
Student: "¿Cuáles son los derechos ARCO en Chile?"
  ↓
RAG Tutor Agent:
  1. Retrieve top 3 sources from vector DB (Ley 21.719, LGPD, etc)
  2. Generate answer from sources
  3. Cite: "Según Ley 21.719 art. X: ..."
  4. Return: {answer, sources: [{title, url, date}]}
  ↓
Frontend: Mostrar respuesta + links a fuentes
```

### 4.3 Legal Source Versioning

```json
{
  "id": "ley-21719-v1",
  "title": "Ley 21.719 Protección de Datos Personales",
  "jurisdiction": "Chile",
  "source_type": "law",
  "official_url": "https://bcn.cl/...",
  "version": "1.0",
  "effective_date": "2023-01-01",
  "valid_until": null,
  "summary": "Derechos ARCO...",
  "last_verified": "2024-01-15",
  "verification_by": "Especialista en privacidad",
  "deprecated_reason": null
}
```

---

## Phase 5: Labs & Capstone (Weeks 10-12)

### 5.1 Lab Guide Agent

**Lab Template**:
- Title: "Diseñar una arquitectura de datos con Data Mesh"
- Setup: "Crea un proyecto GCP, fork el repo starter"
- Steps: 5-10 pasos progresivos
- Validation: Checklist de criterios
- Hints: Si fallas → Agente proporciona pista (no solución)

**Lab Guide Agent**:
```python
student_message = "No puedo hacer el paso 3, la query falla"
  ↓
1. Analyze: Paso 3 = "crear tabla dimensional"
2. Check: ¿Q hay errores comunes en paso 3?
3. Provide: Pista + debugging checklist (no código)
4. Escalate: Si sigue atascado → docente humano
```

### 5.2 Capstone Supervisor

**Entrada**: 20+ artefactos capstone
- Business case
- Mapa de capacidades
- Arquitectura C4
- Data governance operating model
- DPIA
- Risk register (security, privacy, AI)
- Model Cards
- Demo funcional
- Plan 2027-2028

**Supervisor Workflow**:
```python
capstone_submission = {
  "business_case.pdf",
  "architecture_c4.drawio",
  "dpia.xlsx",
  "code_github_link",
  ...
}

supervisor = CapstoneAgent()
for artifact in capstone_submission:
  result = supervisor.validate(artifact)
  # ✓ Accepted | ⚠ Needs revision | ❌ Rejected
  
  if rejected:
    feedback = supervisor.generate_feedback()
    # "Tu DPIA no cubre transferencias internacionales"
```

---

## Phase 6: Admin Panel (Week 13)

### 6.1 Docente Dashboard

```
/admin/master
├── Lecciones
│   ├── Crear nueva
│   ├── Editar
│   └── Queue de revisión (draft → expert_review → legal_review → approved → published)
├── Laboratorios
│   ├── Crear + asignar rubricas
│   ├── Ver submisiones
│   └── Calificar
├── Evaluaciones
│   ├── Quizzes automáticos
│   ├── Case studies (revisión humana)
│   └── Artefactos (Capstone Supervisor)
├── Estudiantes
│   ├── Cohortes
│   ├── Progreso (% completion, badges)
│   └── Notas
├── Referencias legales
│   ├── Versiones
│   ├── Vigencia
│   └── Deprecaciones
└── Reportes
    ├── Tasa de compleción
    ├── Aprobación promedio
    └── Artefactos completados
```

### 6.2 Admin Features

- **Bulk import**: Cargar 12 meses desde JSON
- **Versionado**: Cada cambio = nueva versión (audit trail)
- **Approval workflow**: draft → review → approved → published
- **A/B Testing**: 2 versiones de lesson, medir engagement
- **Metrics**: Tiempo en lección, tasa abandono, asistencia labs

---

## Phase 7: Frontend Pages (Ongoing)

### 7.1 Pages to Create

1. **Landing** (`/master`)
   - Hero + CTA
   - Malla preview
   - Testimonios
   - FAQ

2. **Curriculum** (`/master/curriculum`)
   - Tabla 12 meses
   - Filtros por dominio
   - Download PDF

3. **Month Detail** (`/master/mes-{n}`)
   - Módulos
   - Learning outcomes
   - Deliverables
   - Certifications

4. **Module Content** (`/master/mes-{n}/{module}`)
   - Lecciones (desde DB)
   - Labs interactivos
   - Evaluaciones
   - RAG Tutor chat

5. **Capstone** (`/master/capstone`)
   - Brief Retail LATAM
   - Artefactos requeridos
   - Timeline
   - Submittal

6. **Student Dashboard** (`/master/mi-progreso`)
   - Malla con progreso
   - Calificaciones
   - Badges
   - Próximas entregas

---

## Implementation Constraints

### Legal/Compliance

- ✅ Parafrasear estándares (no copiar texto protegido)
- ✅ Citar fuentes oficiales en todo contenido regulatorio
- ✅ Disclaimer: "Master comercial, no grado académico oficial"
- ✅ No generar asesoría legal automática
- ✅ Mantener versionado de fuentes legales
- ❌ No afirmar acreditación TOGAF/ISO sin convenio

### Technical

- **Agents**: FastAPI + Ollama (local) or Claude API (cloud)
- **Vector DB**: Weaviate o Pinecone (RAG Tutor)
- **Frontend**: HTML/JS + Web Components (reutilizable)
- **Database**: PostgreSQL con audit trail
- **Storage**: GCS para PDFs, código, artefactos
- **CI/CD**: GitHub Actions + Terraform (deploy to GCP)

### Timeline

| Phase | Weeks | Deliverable |
|-------|-------|------------|
| 1: Agents + API | 1-2 | 6 agentes, endpoints core |
| 2: DB + Landing | 3-4 | Schema, landing page |
| 3: Instructor | 5-7 | Primeras 3 lecciones (mes 1) |
| 4: RAG + Legal | 8-9 | Tutor funcionando, 5+ fuentes |
| 5: Labs + Capstone | 10-12 | 3 labs, Capstone Supervisor |
| 6: Admin Panel | 13 | CRUD completo, aprobaciones |
| 7: Frontend | Ongoing | Páginas estudiante |
| 8: Beta Cohort | Week 14+ | Primera cohorte con contenido |

---

## Success Criteria

- [ ] Especificación JSON completamente procesada
- [ ] 6 agentes funcionando (sin errores en 100 ejecuciones)
- [ ] Contenido de mes 1 (4 módulos, 12 lecciones) publicado
- [ ] RAG Tutor responde 10+ preguntas con citas
- [ ] 5+ laboratorios funcionales
- [ ] Capstone Supervisor valida 20+ artifacts
- [ ] Admin panel permite crear/editar/publicar
- [ ] Legal review = 0 infracciones (no copiar ISO, disclaimers, citas)
- [ ] Primera cohorte con 50+ estudiantes
- [ ] Tasa compleción >70%, aprobación >80%

---

## Next Steps

1. **Confirm**: ¿Proceder con todas las 6 agentes o MVP (3)?
2. **Database**: PostgreSQL local o GCP Cloud SQL?
3. **RAG Sources**: ¿Qué 10 fuentes priorizar para V1?
4. **Timeline**: ¿14 semanas realista o ajustar scope?
5. **Budget**: ¿Cloud (Claude, Pinecone) o local (Ollama, Weaviate)?
