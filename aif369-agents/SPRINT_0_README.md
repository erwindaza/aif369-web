# SPRINT 0: Foundation - Getting Started

## What's Done

✅ **3 Master Program Agents Created**:
- `Instructor Agent` → Generates lessons, labs, quizzes
- `Evaluator Agent` → Grades submissions with rubrics
- `Compliance Agent` → Reviews content before publication

✅ **FastAPI Endpoints** (11 routes):
- Lesson generation (async + blocking)
- Lab generation
- Assessment evaluation
- Compliance review
- Health check

✅ **PostgreSQL Schema**:
- 25+ tables (curriculum, content, students, progress, capstone, legal sources, audit)
- Indexes on critical paths
- Versioning + audit trail

✅ **Tests** (6 test cases):
- Instructor generates lesson ✓
- Instructor generates lab ✓
- Evaluator grades quiz ✓
- Compliance detects copyright ✓
- Compliance approves good content ✓
- Compliance rejects false claims ✓

---

## Quick Start (Local Development)

### 1. Prerequisites

```bash
# Install Ollama (free, local LLM)
# Download: https://ollama.ai

# Install PostgreSQL (14+)
brew install postgresql

# Python 3.11+
python --version
```

### 2. Setup Environment

```bash
cd /Users/macbookpro/dev/aif369-web/aif369-agents

# Create venv
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Start Ollama (If not running)

```bash
# In separate terminal
ollama serve

# In another terminal, pull models
ollama pull mistral:7b
ollama pull llama2:70b  # Optional, for testing
```

### 4. Setup PostgreSQL

```bash
# Start PostgreSQL
brew services start postgresql

# Create database
psql -U postgres -c "CREATE DATABASE aif369_master;"

# Initialize schema
psql -U postgres -d aif369_master -f db/schema.sql

# Verify
psql -U postgres -d aif369_master -c "\dt"  # Should list 25+ tables
```

### 5. Run Tests

```bash
# Run all tests
pytest tests/test_master_agents.py -v

# Or specific test
pytest tests/test_master_agents.py::test_instructor_agent_generates_lesson -v

# Expected output:
# test_instructor_agent_generates_lesson PASSED
# test_instructor_agent_generates_lab PASSED
# test_evaluator_agent_grades_quiz PASSED
# test_compliance_agent_detects_copyright PASSED
# test_compliance_agent_approves_good_content PASSED
# test_compliance_agent_rejects_false_claims PASSED
```

### 6. Start API Server

```bash
# Development mode (with auto-reload)
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or production
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 7. Test the API

```bash
# Health check
curl http://localhost:8000/api/master/health

# Generate lesson (blocking)
curl -X POST http://localhost:8000/api/master/lessons/and-wait \
  -H "Content-Type: application/json" \
  -d '{
    "month": 1,
    "module": "Enterprise Architecture Fundamentals",
    "learning_objectives": ["Understand TOGAF ADM", "Apply architecture principles"],
    "topic": "TOGAF Framework Overview",
    "difficulty": "beginner"
  }'

# Expected: JSON lesson with sections, examples, references

# Evaluate quiz
curl -X POST http://localhost:8000/api/master/assess/and-wait \
  -H "Content-Type: application/json" \
  -d '{
    "type": "quiz",
    "submission": "A",
    "expected": "A"
  }'

# Expected: {"status": "success", "output": {"score": 100, "feedback": "✓ Correcto"}}

# Review compliance
curl -X POST http://localhost:8000/api/master/compliance/review/and-wait \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Los sistemas de información requieren controles. Fuente: ISO/IEC 27001:2022",
    "type": "lesson"
  }'

# Expected: {"status": "success", "output": {"review": {"status": "approved", ...}}}
```

---

## What Happens Next (SPRINT 1)

Once SPRINT 0 is working:

1. **Run Instructor Agent in Batch**:
   - Generate 24 lessons (Months 1-6, 4 modules each)
   - Generate 12 labs (2 per month)
   - Run compliance check on all
   - Time: ~2-3 hours

2. **Expert Review**:
   - Queue lessons for human expert review
   - Docente reviews content (accuracy, examples, citations)
   - Approve or request changes

3. **Load into Database**:
   - Publish Month 1 to DB
   - Make live for students

---

## Troubleshooting

### "Cannot connect to Ollama"

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# If not, start it
ollama serve

# Set environment variable if using different port
export OLLAMA_HOST=http://localhost:11434
```

### "PostgreSQL connection refused"

```bash
# Check PostgreSQL is running
pg_isready -U postgres

# Start it
brew services start postgresql

# Or create user/DB manually
psql -U postgres
  CREATE DATABASE aif369_master;
  \c aif369_master
  \i db/schema.sql
```

### "Module not found: agents.instructor_agent"

```bash
# Make sure you're in the right directory
cd /Users/macbookpro/dev/aif369-web/aif369-agents

# Verify agents/ folder exists and has __init__.py
ls agents/__init__.py

# Re-install package
pip install -e .
```

### "Tests fail with timeout"

```bash
# If tests timeout, Ollama/API is too slow
# Try with shorter timeout in tests
# Or increase available CPU/RAM to local machine
```

---

## Files Created in SPRINT 0

```
aif369-agents/
├── agents/
│   ├── instructor_agent.py      # ← Generate lessons/labs/quizzes
│   ├── evaluator_agent.py       # ← Grade submissions
│   ├── compliance_agent.py      # ← Review before publish
│   └── __init__.py              # ← Updated exports
├── api/
│   └── routes/
│       └── master.py            # ← 11 FastAPI routes
├── db/
│   └── schema.sql               # ← 25+ PostgreSQL tables
├── tests/
│   └── test_master_agents.py    # ← 6 test cases
└── SPRINT_0_README.md           # ← This file
```

---

## Success Criteria (Check These)

- [ ] `pytest tests/test_master_agents.py` → All tests PASS
- [ ] `curl http://localhost:8000/api/master/health` → 200 OK
- [ ] `curl ... /api/master/lessons/and-wait` → Returns lesson JSON in <60 seconds
- [ ] `curl ... /api/master/assess/and-wait` → Returns score + feedback in <10 seconds
- [ ] `curl ... /api/master/compliance/review/and-wait` → Returns review status in <5 seconds
- [ ] PostgreSQL tables created: `psql -d aif369_master -c "\dt"` → 25+ tables

---

## Next Steps

Once all above ✓, you're ready for **SPRINT 1**:

1. Run batch lesson generation (Instructor Agent, ~2-3 hours)
2. Review content with Compliance Agent
3. Schedule expert human review
4. Publish Month 1 to database
5. Create student portal (landing page, signup)

---

## Questions?

- Check logs: `tail -f logs/aif369-agents.log`
- Test agent directly: `python -c "from agents import InstructorAgent; ..."`
- Debug endpoint: Add `--log-level debug` to uvicorn command

**Status**: ✓ SPRINT 0 Complete — Ready to Generate Content!
