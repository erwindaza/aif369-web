# AIF369 Master - Execution Roadmap
## Aggressive Plan: Full Stack in 12 Weeks

**Timeline**: Aug 3 - Oct 28, 2026  
**Status**: SPRINT 0 (Foundation) - Week 1  
**Approach**: Parallel agents, incremental content, publish-early strategy

---

## SPRINT 0: Foundation (Week 1: Aug 3-9)
### Mission: Setup infrastructure, create 3 new agents, API skeleton

#### Goals
- [ ] Docker Desktop fixed ✓ (resolve later if blocked)
- [ ] 3 Master agents created (Instructor, Evaluator, Compliance)
- [ ] FastAPI backend skeleton with 10 core endpoints
- [ ] PostgreSQL schema (tables for lessons, labs, assessments, capstone)
- [ ] Master content loader (parse JSON → DB)
- [ ] First GitHub actions workflow (test agents)

#### Agents to Create
1. **Instructor Agent** (FastAPI endpoint)
   - Input: {month: int, module: str, learning_objective: str}
   - Output: lesson.json with sections, examples, knowledge_check
   - Model: Mistral 7B (fast) or Claude (better quality)
   - Constraints: Paraphrase TOGAF/ISO, cite sources
   
2. **Evaluator Agent** (FastAPI endpoint)
   - Input: {submission: str, rubric: dict, expected_output: str}
   - Output: {score: int, feedback: str, areas_to_improve: []}
   - Model: Mistral 7B
   - Constraints: Fair, constructive, cite rubric criteria

3. **Compliance Agent** (FastAPI endpoint)
   - Input: {content: str, type: enum(lesson|lab|capstone)}
   - Output: {status: enum(approved|needs_review|rejected), issues: []}
   - Model: Claude (more careful)
   - Checks:
     - ✓ Cites sources in legal content?
     - ✓ No copyright ISO/TOGAF text?
     - ✓ Includes disclaimer for "Master comercial"?
     - ✓ No false accreditation claims?

#### Tasks (Parallel)

**Backend Team** (You + AI)
```
backend/
├── models/
│   ├── master_models.py ✓ (DONE)
│   └── api_schemas.py (NEW - Pydantic for API)
├── agents/
│   ├── instructor_agent.py (NEW)
│   ├── evaluator_agent.py (NEW)
│   ├── compliance_agent.py (NEW)
│   └── master_orchestrator.py (NEW - coordinates all 3)
├── api/
│   ├── routes/
│   │   ├── lessons.py (POST /api/master/lessons)
│   │   ├── assessments.py (POST /api/master/assess)
│   │   └── admin.py (POST /api/admin/content/review)
│   └── dependencies.py
├── db/
│   ├── schema.sql (PostgreSQL DDL)
│   └── migrations/
│       └── 001_master_initial.sql
└── utils/
    └── json_loader.py (load aif369_master_data_ai_governance.json)
```

**Database Setup**
```sql
-- PostgreSQL local + Cloud SQL prod
CREATE TABLE programs (...);
CREATE TABLE months (...);
CREATE TABLE modules (...);
CREATE TABLE lessons (...);
CREATE TABLE assessments (...);
CREATE TABLE capstones (...);
-- See MASTER_IMPLEMENTATION_PLAN.md for full schema
```

**Tests**
```python
tests/
├── test_instructor_agent.py (does it generate valid JSON?)
├── test_evaluator_agent.py (does it score fairly?)
├── test_compliance_agent.py (does it catch violations?)
└── test_api_endpoints.py (200 OK?)
```

#### Deliverables (Sprint 0 End)
- [ ] 3 agents ready (can call via FastAPI)
- [ ] DB schema migrated (empty tables)
- [ ] API skeleton (10 endpoints, return mock data)
- [ ] GitHub Actions workflow (run tests on push)
- [ ] 2 sample lessons generated + passed compliance ✓
- [ ] README: How to run locally + deploy to GCP

#### Success Criteria
- `pytest tests/` = all green
- `curl localhost:8000/api/master/health` = 200
- Instructor Agent generates 100-word lesson in <5 sec
- Compliance Agent reviews lesson in <2 sec
- No syntax errors in agent code

---

## SPRINT 1: Agents at Scale (Weeks 2-3: Aug 10-23)
### Mission: Run agents to generate Months 1-6 content

#### Goals
- [ ] Lessons generated: 24 (4 modules × 6 months)
- [ ] Labs generated: 12 (2 per month)
- [ ] All content passes Compliance Agent ✓
- [ ] Expert review queue established (humans review top-3 per month)
- [ ] Month 1 approved and loaded into DB

#### Workflow

```
FOR month IN [1, 2, 3, 4, 5, 6]:
  FOR module IN curriculum[month].modules:
    # Generate lesson
    lesson = instructor_agent.generate(
      month=month,
      module=module,
      learning_objectives=curriculum[month][module].objectives
    )
    # Save as draft
    db.lessons.insert({...lesson, status='draft'})
    
    # Run compliance check
    compliance = compliance_agent.review(lesson.content)
    IF compliance.status == 'rejected':
      log(compliance.issues)  # Admin to fix manually
    ELIF compliance.status == 'approved':
      lesson.status = 'expert_review'  # Queue for human expert
    
    # Generate knowledge check
    knowledge_check = instructor_agent.gen_quiz(lesson)
    lesson.questions = knowledge_check

  # Generate 2 labs per month
  FOR i IN [1, 2]:
    lab = instructor_agent.generate_lab(
      month=month,
      topic=random_from_month.topics,
      difficulty=i
    )
    lab.status = 'expert_review'
    db.labs.insert(lab)
```

#### Parallel Execution

**Agent 1: Instructor** (Generate lessons in parallel)
```bash
# Run async - 4 lessons/month × 6 months = 24 lessons
# Batch process: instructor_agent.batch_generate(months=[1,2,3,4,5,6])
# Time: ~2 hours (if 5 min/lesson)
```

**Agent 2: Lab Generator** (Parallel to lessons)
```bash
# Generate 2 labs/month × 6 months = 12 labs
# Async: lab_generator.batch_generate(months=[1,2,3,4,5,6])
# Time: ~1 hour
```

**Agent 3: Compliance** (Background check all)
```bash
# Review 24 lessons + 12 labs = 36 items
# Parallel: compliance_agent.batch_review(content_queue)
# Time: ~1 hour (2 sec per item)
# Output: Rejection rate (target <5%)
```

**Human: Expert Review** (Ongoing, prioritize Month 1)
```
Queue: 36 items in 'expert_review' status
Expert: Data architect reviews 1-2 per day
Focus: Is content accurate? Examples good? Paraphrasing OK?
Output: expert_review → approved (or back to draft)
```

#### Deliverables (Sprint 1 End)
- [ ] 24 lessons in DB (status: approved or expert_review)
- [ ] 12 labs in DB
- [ ] Month 1 fully approved & published
- [ ] Admin dashboard shows review queue
- [ ] Metrics: avg compliance score, expert feedback counts
- [ ] GitHub: All committed with audit trail

#### Success Criteria
- Month 1: 4 lessons + 2 labs all approved
- Compliance pass rate: >85%
- Generation time: <3 hours for 6 months
- Zero copyright violations detected
- Expert reviewers have <10 hours total work

---

## SPRINT 2: Landing + Portal (Weeks 4-5: Aug 24 - Sep 6)
### Mission: Public-facing website ready for signups

#### Goals
- [ ] Landing page live at /master
- [ ] Curriculum page (malla visual)
- [ ] Student portal skeleton (login, dashboard)
- [ ] Email capture for waitlist
- [ ] SEO keywords indexed

#### Frontend Stack
- **Pages**: HTML + JS (match existing aif369.com style)
- **Components**: Hero, curriculum grid, FAQ accordion
- **Styling**: Tailwind (or existing CSS)
- **Database**: Students table (name, email, cohort preference)

#### Pages to Build

1. **Landing** (`/master`)
   ```html
   - Hero: "Master en Arquitectura, Gobernanza de Datos e IA"
   - Disclaimer: "Master comercial, no grado académico oficial"
   - 12 meses, 420h, 8 dominios
   - Audience: Data/AI Architects, CDOs, CIOs
   - CTA: "Reserva tu lugar" → email signup
   - Malla preview (clickable → /master/curriculum)
   - Testimonios (placeholder)
   - FAQ
   - Pricing (TBD)
   - Contact for info
   ```

2. **Curriculum** (`/master/curriculum`)
   ```html
   - Interactive table: 12 months
   - Columns: Month, Title, Modules, Learning Outcomes, Hours
   - Filters: By domain, by certification
   - Click month → /master/mes-{n}
   - Download: PDF, Excel
   ```

3. **Month Detail** (`/master/mes-{n}`)
   ```html
   - Month title + brief
   - Modules (4 per month)
     - Module title
     - Learning objectives (list)
     - Lessons (links to /master/mes-{n}/modulo-{m})
   - Deliverables
   - Certifications aligned
   - Next month CTA
   ```

4. **Lesson View** (`/master/mes-{n}/modulo-{m}`)
   ```html
   - Lesson title, duration, learning objectives
   - Content sections (from DB)
   - Diagram (embedded Mermaid)
   - Examples
   - Activity button → /master/activity/{lesson_id}
   - Knowledge check: 5 questions (quiz)
   - Lab link (if exists)
   - References (clickable, opens legal_sources)
   ```

5. **Student Dashboard** (`/master/mi-progreso`)
   ```html
   - Login required
   - Malla with progress: [ ], [√], [!]
   - Completed lessons, badges
   - Next due: lab, assessment
   - Grades (when available)
   - Capstone status (when month 12)
   ```

#### Backend Endpoints (New)

```bash
# Public
GET  /api/master/curriculum       # Full tree
GET  /api/master/mes/{n}          # Month detail
GET  /api/master/lesson/{id}      # Lesson content
GET  /api/master/legal-sources    # Versioned references

# Student (requires login)
POST /api/student/login           # Email signup
GET  /api/student/progress        # {lessons: {completed}, labs: {}}
POST /api/student/activity        # Submit activity
POST /api/student/quiz            # Submit quiz

# Admin
GET  /api/admin/dashboard         # Stats
```

#### Deliverables (Sprint 2 End)
- [ ] Landing live (Vercel deployment)
- [ ] 100+ email signups
- [ ] Curriculum page SEO-optimized
- [ ] Student login working
- [ ] Month 1 content visible to logged-in students
- [ ] GitHub: HTML, CSS, JS, API routes committed

#### Success Criteria
- Landing loads in <2s
- Mobile responsive
- All links work (no 404s)
- Email signup: <5 second form
- Curriculum page: <1s to load

---

## SPRINT 3: RAG Tutor + Legal Sources (Weeks 6-7: Sep 7-20)
### Mission: Knowledge assistant with citations

#### Goals
- [ ] Vector DB (Weaviate or Pinecone) set up
- [ ] 20+ legal/reference sources indexed (versioned)
- [ ] RAG Tutor Agent created + tested
- [ ] Tutor chat embedded in lesson pages
- [ ] Citation accuracy >95%

#### RAG Tutor Components

1. **Legal Sources Library**
   ```json
   [
     {
       "id": "ley-21719-v1",
       "title": "Ley 21.719 Protección de Datos Personales",
       "jurisdiction": "Chile",
       "official_url": "https://bcn.cl/...",
       "version": "1.0",
       "effective_date": "2023-01-01",
       "summary": "Derechos ARCO, principios de tratamiento...",
       "topics": ["privacidad", "derechos-titulares", "consentimiento"],
       "last_verified": "2024-08-01"
     },
     {
       "id": "iso-27001-2022-summary",
       "title": "ISO/IEC 27001:2022 - Information Security Management",
       "source_type": "standard",
       "url": "https://iso.org/standard/27001",
       "summary": "Paraphrased: ISMS establishes controls for confidentiality, integrity, availability...",
       "topics": ["seguridad", "isms", "controles"]
     },
     // + 18 more (TOGAF, NIST, GDPR, DAMA, etc)
   ]
   ```

2. **Vector DB Index**
   ```
   Weaviate / Pinecone instance
   Collection: "master-legal-sources"
   - Chunk documents into 500-token sections
   - Embed with text-embedding-3-small
   - Index: source_id, chunk_id, topic, jurisdiction
   ```

3. **RAG Tutor Agent**
   ```python
   class RAGTutorAgent:
     def answer(self, question: str) -> {answer, sources, confidence}:
       1. Retrieve top-3 sources (similarity search)
       2. Filter by relevance (threshold >0.7)
       3. Generate answer from sources (Claude)
       4. Cite: "Según Ley 21.719 Art. X: ..."
       5. Return with links to source + verification date
   ```

4. **Frontend Integration**
   ```html
   <!-- In lesson page -->
   <div class="rag-tutor">
     <input placeholder="Pregunta sobre este tema...">
     <button>Consultar</button>
     <div class="response">
       <p>Respuesta con citas...</p>
       <div class="sources">
         <a href="/legal-sources/ley-21719-v1">Ley 21.719 (vigente 2023)</a>
         <a href="/legal-sources/iso-27001-2022">ISO/IEC 27001:2022</a>
       </div>
     </div>
   </div>
   ```

#### Tasks (Parallel)

**RAG Setup** (2-3 days)
- [ ] Create Weaviate Docker container (or Pinecone account)
- [ ] Load 20+ sources (paraphrase + cite)
- [ ] Create embedding pipeline
- [ ] Test retrieval accuracy

**Tutor Agent** (3-4 days)
- [ ] Implement retrieval logic
- [ ] Implement generation (Claude API or Mistral)
- [ ] Test citation accuracy (manual validation)
- [ ] Add fallback for out-of-scope questions

**Frontend** (2-3 days)
- [ ] Chat widget (HTML + JS)
- [ ] Source attribution UI
- [ ] Error handling (no results, rate limit)
- [ ] Mobile responsive

#### Deliverables (Sprint 3 End)
- [ ] RAG Tutor responds to 20+ test questions (human validates)
- [ ] 20+ legal sources versioned in DB
- [ ] Chat widget live on lesson pages
- [ ] Citation accuracy measured: >95%
- [ ] Unit tests for RAG pipeline

#### Success Criteria
- RAG response time: <3 seconds
- Citation accuracy: >95%
- Source links work (no 404s)
- Can answer: "¿Cuáles son los derechos ARCO en Chile?" (with Ley 21.719)
- Can answer: "¿Qué es TOGAF?" (with paraphrasing, not copy)

---

## SPRINT 4: Labs + Hands-On (Weeks 8-9: Sep 21 - Oct 4)
### Mission: 12 working laboratorios (1-2 per month)

#### Goals
- [ ] 12 labs created, tested, deployed
- [ ] Lab environments (Docker, GCP, local)
- [ ] Lab Guide Agent working
- [ ] Student submissions working
- [ ] Auto-grading for <50% of labs

#### Lab Types

1. **Cloud Architecture Lab** (Months 1-2)
   - Design a 3-tier architecture on GCP
   - Use Terraform
   - Starter: GitHub template
   - Validation: `terraform validate` + custom checks

2. **Data Governance Lab** (Months 3-4)
   - Build data catalog with metadata
   - Starter: PostgreSQL + Python
   - Tools: dbt, Apache Atlas
   - Validation: Glosario completo, lineage correcto

3. **Security & Privacy Lab** (Months 5-6)
   - Implement ISO 27001 controls checklist
   - Create DPIA for sample system
   - Tools: Spreadsheet + Risk register template
   - Validation: All controls documented

4. **AI Governance Lab** (Months 9-10)
   - Build Model Card + System Card
   - Evaluate LLM outputs
   - Tools: JSON + Red team checklist
   - Validation: Cards complete, evaluations reasonable

#### Lab Guide Agent

```python
class LabGuideAgent:
  def hint(self, lab_id, step_num, student_problem):
    """Provide hint without solution"""
    1. Understand step from lab spec
    2. Understand student's problem (from description/error)
    3. Generate hints (not solution):
       - "Check if your terraform file has the 'resource' block"
       - "The metadata should include tags for data classification"
       - "Look at step 2 again for how to initialize the tool"
    4. Suggest next debugging step
    5. Escalate to human if repeated failures
```

#### Lab Submission Workflow

```
Student submits lab
  ↓
Auto-grade:
  - Code syntax: valid?
  - Tests: pass?
  - Required artifacts: present?
  ↓
IF auto-passed:
  Status = 'approved'
  Points = 100
ELSE:
  Status = 'needs_review'
  Assign to: Lab Guide Agent for hint OR human reviewer
  ↓
Student revises
  ↓
RE-SUBMIT
```

#### Deliverables (Sprint 4 End)
- [ ] 12 labs in DB (all with instructions, starter code, solution)
- [ ] Lab submission form working
- [ ] Lab Guide Agent responds to 50+ test queries
- [ ] Auto-grading works for 50% of submissions
- [ ] Lab scoreboard (student progress)

#### Success Criteria
- 12 labs deployed and tested
- Average lab time: within 2h of estimate
- Student satisfaction: >4/5 (on feedback form)
- Guide Agent helps 80% without escalation

---

## SPRINT 5: Capstone Supervisor (Weeks 10-11: Oct 5-18)
### Mission: Full capstone project management

#### Goals
- [ ] Capstone spec finalized (Retail LATAM Agentic)
- [ ] 20+ artifact templates created + downloadable
- [ ] Capstone Supervisor Agent working (validates artifacts)
- [ ] Submission form + tracker live
- [ ] Rubric + scoring complete

#### Capstone Artifacts (20+)

```
1. Business case (2-3 pages)
2. Capability map (diagram)
3. Architecture current state (C4)
4. Architecture target (C4)
5. TOGAF ADM overview (1 page)
6. ArchiMate model (diagram)
7. Data governance operating model
8. Data catalog (structure)
9. Business glossary (sample, 50 terms)
10. Data quality scorecard
11. RoPA (record of processing activities)
12. DPIA (data impact assessment)
13. Flujo de derechos (ARCO rights fulfillment)
14. SGSI scope + objectives
15. Risk register (security + privacy + AI)
16. Statement of Applicability (SoA)
17. AI inventory
18. AI impact assessment
19. Model Cards (3+ models)
20. Threat model
21. Control matrix
22. Plan de observabilidad
23. Roadmap 2027-2028
24. GitHub repo (working code)
25. Demo funcional (video + instructions)
```

#### Capstone Supervisor Agent

```python
class CapstoneAgent:
  def validate_artifact(self, artifact_id, artifact_content):
    """Validate single capstone artifact"""
    
    if artifact_type == 'business_case':
      check:
        - Business objectives clear?
        - Capabilities identified?
        - Success metrics defined?
      
    elif artifact_type == 'architecture_c4':
      check:
        - 4 diagrams (context, containers, components, code)?
        - Technology choices justified?
        - Trade-offs documented?
      
    elif artifact_type == 'dpia':
      check:
        - Data flows mapped?
        - Risks assessed (H/M/L)?
        - Mitigations defined?
        - Residual risk acceptable?
    
    elif artifact_type == 'ai_inventory':
      check:
        - All systems documented?
        - Risk classification (high/medium/low)?
        - Impact assessment complete?
    
    return {
      status: 'approved' | 'needs_revision' | 'rejected',
      feedback: str,
      score: int (0-100),
      next_steps: [str]
    }
  
  def validate_capstone(self, student_id):
    """Validate all 20+ artifacts together"""
    1. Load all artifacts from DB
    2. Run validate_artifact on each
    3. Check completeness: all 20 submitted?
    4. Check coherence: 
       - Architecture matches business case?
       - Risks in risk register covered by controls?
       - Data in catalog covered by DPIA?
    5. Final status: 
       - All approved → PASS
       - <2 rejected → Resubmit + regrade
       - >2 rejected → FAIL (redo capstone)
```

#### Deliverables (Sprint 5 End)
- [ ] Capstone spec published
- [ ] 25 artifact templates created + downloadable (Draw.io, Excel, Markdown)
- [ ] Submission form live
- [ ] Capstone Supervisor Agent passing 10+ validations
- [ ] Rubric & scoring sheet
- [ ] Capstone tracker dashboard (admin view)

#### Success Criteria
- All 25 templates downloadable + editable
- Agent validates capstone in <5 minutes
- Student can submit & get feedback in 1 hour
- Artifact validation accuracy >90% (human spot-check)

---

## SPRINT 6: Admin Panel (Weeks 12: Oct 19-25)
### Mission: Complete content management for docentes

#### Goals
- [ ] CRUD for all content (lessons, labs, assessments)
- [ ] Approval workflow (draft → expert_review → legal_review → published)
- [ ] Student management (cohorts, grades, progress)
- [ ] Content versioning (audit trail)
- [ ] Analytics dashboard

#### Admin Features

1. **Content Management**
   ```
   /admin/master
   ├── Lecciones
   │   ├── [+ Crear nueva]
   │   ├── [Filtrar por estado, mes, módulo]
   │   └── [Tabla]
   │       ├── Título
   │       ├── Mes/Módulo
   │       ├── Estado [Draft|Review|Approved|Published]
   │       ├── Creado por
   │       ├── Última modificación
   │       ├── [Edit] [Preview] [Delete]
   │   
   ├── Laboratorios
   ├── Evaluaciones
   ├── Capstone
   └── Plantillas
   ```

2. **Approval Workflow**
   ```
   Status transitions:
   draft
     → [Expert Review]
        ↓
     expert_review
     → [Legal Review]
        ↓
     legal_review
     → [Publish]
        ↓
     published
   
   At each stage:
   - [Approve] → next stage
   - [Request Changes] → back to previous + comment
   - [Reject] → back to draft + reason
   ```

3. **Student Management**
   ```
   /admin/students
   ├── Cohortes
   │   ├── [+ Nueva cohorte]
   │   ├── Tabla:
   │   │   ├── Cohorte ID
   │   │   ├── Inicio fecha
   │   │   ├── Fin fecha
   │   │   ├── # Estudiantes
   │   │   ├── [Editar] [Ver detalles]
   │   │
   │   └── Ver detalles → Estudiantes
   │       ├── Nombre, Email
   │       ├── Progress: 0% → 100%
   │       ├── Lecciones completas / total
   │       ├── Labs: Submitted / Approved
   │       ├── Promedio calificación
   │       ├── [View profile]
   ```

4. **Analytics**
   ```
   /admin/analytics
   ├── Engagement
   │   ├── Lecciones más vistas
   │   ├── Tiempo promedio por lección
   │   ├── Tasa abandono
   │   └── Chat Tutor: Top 10 preguntas
   │
   ├── Performance
   │   ├── Calificación promedio
   │   ├── Tasa aprobación
   │   ├── Distribución de notas
   │   └── Predictores de fracaso
   │
   ├── Content
   │   ├── Lecciones creadas/mes
   │   ├── Aprobación rate
   │   ├── Compliance violations
   │   └── Legal review time avg
   ```

5. **Versioning**
   ```
   Every edit creates version:
   - lesson_001_v1 (Aug 5, by Erwin)
   - lesson_001_v2 (Aug 7, changes title)
   - lesson_001_v3 (Aug 10, expert feedback)
   
   Admin can:
   [Rollback to v2]
   [Compare v1 vs v3]
   [View change history]
   ```

#### Backend Endpoints (Admin)

```bash
# Content CRUD
GET    /api/admin/lessons
POST   /api/admin/lessons
PUT    /api/admin/lessons/{id}
DELETE /api/admin/lessons/{id}
POST   /api/admin/lessons/{id}/approve
POST   /api/admin/lessons/{id}/reject

# Student management
GET    /api/admin/cohorts
POST   /api/admin/cohorts
GET    /api/admin/cohorts/{id}/students
PUT    /api/admin/students/{id}/grade

# Analytics
GET    /api/admin/analytics/engagement
GET    /api/admin/analytics/performance
GET    /api/admin/content/review-queue
```

#### Deliverables (Sprint 6 End)
- [ ] Admin panel fully functional
- [ ] CRUD for all content types
- [ ] Approval workflow tested (full lifecycle)
- [ ] Student roster + progress tracking
- [ ] Analytics dashboard (>5 metrics)
- [ ] Audit trail for all changes

#### Success Criteria
- Load admin dashboard in <2s
- Create lesson end-to-end in <5 min
- Approval workflow handles 100 items/day
- Analytics load in <3s
- No data loss (audit trail >99% coverage)

---

## SPRINT 7: Productionization (Weeks 13-14: Oct 26 - Nov 8)
### Mission: Deploy to production, prepare beta cohort

#### Goals
- [ ] Cloud Run deployment (GCP)
- [ ] Terraform infrastructure
- [ ] GitHub Actions CI/CD
- [ ] PostgreSQL Cloud SQL
- [ ] Vector DB (Weaviate/Pinecone) production
- [ ] Monitoring + alerting
- [ ] Security review

#### Deployment Checklist

```
[ ] Terraform:
    [ ] Cloud Run services (API, Tutor, Admin)
    [ ] Cloud SQL PostgreSQL
    [ ] Weaviate instance (or Pinecone)
    [ ] Storage buckets (PDFs, code, artifacts)
    [ ] IAM roles + service accounts
    [ ] Secrets Manager (API keys, DB creds)

[ ] GitHub Actions:
    [ ] Test agents (pytest)
    [ ] Build Docker image
    [ ] Deploy to Cloud Run
    [ ] Run smoke tests

[ ] Monitoring:
    [ ] Cloud Logging
    [ ] Cloud Monitoring
    [ ] Uptime checks
    [ ] Alert on agent failures
    [ ] Alert on API errors >2%

[ ] Security:
    [ ] SSL/TLS certificates
    [ ] DDoS protection
    [ ] SQL injection prevention (use ORM)
    [ ] XSS prevention (escape HTML)
    [ ] CSRF protection
    [ ] Rate limiting (tutor: 100/hour per user)
    [ ] Auth (email login, session tokens)

[ ] Compliance:
    [ ] Privacy policy updated
    [ ] Terms of service
    [ ] Data retention policy
    [ ] GDPR/Ley 21.719 compliance
```

#### Deliverables (Sprint 7 End)
- [ ] Production environment live (aif369.com/master)
- [ ] All infrastructure as code (Terraform)
- [ ] CI/CD working (automated tests + deployment)
- [ ] Monitoring + alerting active
- [ ] Security audit passed
- [ ] Documentation (runbook, architecture)

#### Success Criteria
- Uptime: 99.5%
- API latency p95: <500ms
- Zero security vulnerabilities
- All agents responding <3s

---

## SPRINT 8: Beta Cohort (Week 15+: Nov 9+)
### Mission: Launch with 50+ students

#### Goals
- [ ] Marketing (LinkedIn, email, aif369.com)
- [ ] Student onboarding flow
- [ ] First cohort start (Month 1 content)
- [ ] Support system (tutor chat, docente office hours)
- [ ] Feedback collection

#### Cohort Timeline

```
Nov 9: Cohort 1 starts
  - 50 students enrolled
  - Week 1: Month 1 lessons + welcome
  - Week 2: First lab (Cloud Architecture)
  - Week 3: Quiz + feedback from Evaluator Agent

Nov 30: Cohort 1 finishes Month 1
  - Collect feedback: What worked? What didn't?
  - Metrics: Completion rate, avg grade, NPS

Dec 1: Cohort 2 starts
  - Incorporate Month 1 feedback
  - Weeks 2-3: Month 2 content rollout

... continues through September 2027 (12 months)
```

#### Student Support

1. **RAG Tutor** (24/7)
   - Questions answered in <3s
   - Citations provided
   - Escalate to docente if confusion persists

2. **Lab Guide Agent** (24/7)
   - Hints for stuck students
   - Debugging help
   - Escalate if repeated failures

3. **Evaluator Agent** (24/7)
   - Auto-grade submissions
   - Feedback on wrong answers
   - Coaching for improvement

4. **Docente Office Hours** (Weekly)
   - 2h sync sessions
   - Q&A on complex topics
   - Career guidance
   - Group discussions

#### Deliverables (Sprint 8+)
- [ ] Cohort 1 enrolled (50+ students)
- [ ] Marketing materials ready
- [ ] Support system operational
- [ ] Feedback loop established
- [ ] Month 2 content prepared for rollout

#### Success Criteria
- Cohort 1: >75% completion rate
- Student satisfaction: >4.2/5 NPS
- Agents helping >80% without escalation
- Month 1 content fully published

---

## PARALLEL TRACKS (Ongoing)

### Track A: Content Generation (All Sprints)
**Owner**: Instructor Agent + Compliance Agent  
**Output**: 
- 24 more lessons (Months 7-12)
- 12 more labs
- 24 assessments
- All passing compliance review

### Track B: Legal Sources (All Sprints)
**Owner**: Compliance Agent + Human experts  
**Output**:
- Versioned legal sources (20→50+)
- Quarterly updates for laws/regulations
- All sources cited in lessons

### Track C: Community (All Sprints)
**Owner**: Marketing + Docentes  
**Output**:
- LinkedIn content (tips, snippets)
- Student testimonials
- Case study (Retail LATAM Agentic)
- Articles on AI governance trends

---

## METRICS & MONITORING

### Agent Performance
```python
metrics = {
  'instructor_agent': {
    'generation_time_sec': 240,  # 4 min/lesson
    'compliance_pass_rate': 0.92,
    'expert_review_feedback_rate': 0.08,  # 8% need changes
  },
  'evaluator_agent': {
    'grading_time_sec': 5,
    'accuracy_vs_human': 0.94,
    'appeal_rate': 0.02,  # 2% students appeal grade
  },
  'rag_tutor_agent': {
    'response_time_sec': 2.3,
    'citation_accuracy': 0.97,
    'escalation_rate': 0.12,  # 12% escalate to docente
  },
  'lab_guide_agent': {
    'hint_quality_rating': 4.3 / 5,  # student feedback
    'helps_without_spoiling': 0.88,
  },
  'capstone_supervisor_agent': {
    'validation_time_sec': 180,  # 3 min per capstone
    'rejection_rate': 0.08,  # 8% rejected, need redo
  },
  'compliance_agent': {
    'detection_rate': 1.0,  # catches all violations (manual check >1 per day)
    'false_positive_rate': 0.03,
  }
}
```

### Student Metrics
```python
cohort_metrics = {
  'enrollment': 50,
  'completion_rate': 0.77,  # 77% finish all 12 months
  'avg_grade': 81.5,  # out of 100
  'nps': 4.4,  # out of 5
  'time_per_month': 35.5,  # hours
  'lab_pass_rate': 0.89,
  'capstone_pass_rate': 0.73,
}
```

### Infrastructure Metrics
```python
infra_metrics = {
  'api_latency_p50': 120,  # ms
  'api_latency_p95': 480,  # ms
  'error_rate': 0.001,  # 0.1%
  'uptime': 0.9975,  # 99.75%
  'db_connections': 45,  # max 100
  'vector_db_latency': 250,  # ms
}
```

---

## Success Definition

**SPRINT 0-2**: ✓ Agents working, content generation automated  
**SPRINT 3-5**: ✓ Students can learn, practice, evaluate selves  
**SPRINT 6-7**: ✓ Docentes can manage, admin can approve  
**SPRINT 8+**: ✓ Real students, real feedback, real impact  

---

## Open Questions (Decide Now)

1. **Database**: PostgreSQL local (for Sprints 0-5) or GCP Cloud SQL immediately?
2. **LLM Model**: Mistral 7B (fast, free) or Claude API (better quality, costs)?
3. **Vector DB**: Weaviate (open source) or Pinecone (SaaS)?
4. **Pricing Model**: Free beta, then paid? Freemium?
5. **Certification**:  Can we offer a certificate or not?
6. **First Content**: Start with Month 1 (Foundations) or Month 12 (Capstone)?

---

## Next Action

**RIGHT NOW (Next 2 hours)**:

1. ✓ Fix Docker Desktop (try again or skip to local Ollama)
2. [ ] Decide: MVP (Sprints 0-3) vs Full (Sprints 0-8)?
3. [ ] Decide: Database, LLM, Vector DB
4. [ ] Create agents/instructor_agent.py (first Instructor Agent)
5. [ ] Test with 1 sample lesson generation

**Go/No-Go**: Is this plan realistic? Do you want to modify anything?

---

**SPRINT 0 STARTS NOW. LET'S GO.**
