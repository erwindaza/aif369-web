-- AIF369 Master Program Database Schema
-- PostgreSQL 14+

-- ─────────────────────────────────────────────────────────────
-- Program & Curriculum
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS programs (
  id TEXT PRIMARY KEY,
  official_name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  brand TEXT,
  duration_months INTEGER,
  recommended_hours INTEGER,
  status TEXT DEFAULT 'draft', -- draft | published | archived
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS months (
  id TEXT PRIMARY KEY,
  program_id TEXT REFERENCES programs(id),
  month_number INTEGER NOT NULL CHECK (month_number >= 1 AND month_number <= 12),
  title TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS modules (
  id TEXT PRIMARY KEY,
  month_id TEXT REFERENCES months(id),
  title TEXT NOT NULL,
  position INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────
-- Content (Lessons, Labs, Assessments)
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS lessons (
  id TEXT PRIMARY KEY,
  month_id TEXT REFERENCES months(id),
  module_id TEXT REFERENCES modules(id),
  title TEXT NOT NULL,
  summary TEXT,
  estimated_minutes INTEGER,
  content TEXT,  -- JSON
  learning_objectives TEXT,  -- JSON array
  status TEXT DEFAULT 'draft', -- draft | expert_review | legal_review | approved | published | deprecated
  requires_legal_review BOOLEAN DEFAULT FALSE,
  created_by TEXT,
  reviewed_by TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  reviewed_at TIMESTAMP,
  published_at TIMESTAMP,
  version INTEGER DEFAULT 1
);

CREATE INDEX idx_lessons_month ON lessons(month_id);
CREATE INDEX idx_lessons_status ON lessons(status);
CREATE INDEX idx_lessons_version ON lessons(id, version);

CREATE TABLE IF NOT EXISTS labs (
  id TEXT PRIMARY KEY,
  month_id TEXT REFERENCES months(id),
  title TEXT NOT NULL,
  description TEXT,
  difficulty TEXT, -- beginner | intermediate | advanced
  estimated_hours FLOAT,
  setup_instructions TEXT,
  steps TEXT,  -- JSON array
  validation_criteria TEXT,  -- JSON array
  tools_required TEXT,  -- JSON array
  status TEXT DEFAULT 'draft',
  created_by TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  version INTEGER DEFAULT 1
);

CREATE INDEX idx_labs_month ON labs(month_id);
CREATE INDEX idx_labs_status ON labs(status);

CREATE TABLE IF NOT EXISTS assessments (
  id TEXT PRIMARY KEY,
  month_id TEXT REFERENCES months(id),
  title TEXT NOT NULL,
  type TEXT NOT NULL, -- quiz | case_study | artifact_review
  description TEXT,
  estimated_minutes INTEGER,
  questions TEXT,  -- JSON array
  rubric TEXT,  -- JSON object {criterion: weight}
  passing_score INTEGER DEFAULT 70,
  status TEXT DEFAULT 'draft',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_assessments_month ON assessments(month_id);
CREATE INDEX idx_assessments_type ON assessments(type);

-- ─────────────────────────────────────────────────────────────
-- Student Data
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS cohorts (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  program_id TEXT REFERENCES programs(id),
  start_date DATE NOT NULL,
  end_date DATE,
  max_students INTEGER DEFAULT 50,
  status TEXT DEFAULT 'planning', -- planning | active | completed | archived
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS students (
  id TEXT PRIMARY KEY,
  cohort_id TEXT REFERENCES cohorts(id),
  email TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  status TEXT DEFAULT 'enrolled', -- enrolled | active | completed | dropped | failed
  enrollment_date TIMESTAMP DEFAULT NOW(),
  completion_date TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_students_cohort ON students(cohort_id);
CREATE INDEX idx_students_email ON students(email);

-- ─────────────────────────────────────────────────────────────
-- Student Progress & Grades
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS student_lessons (
  id TEXT PRIMARY KEY,
  student_id TEXT REFERENCES students(id),
  lesson_id TEXT REFERENCES lessons(id),
  status TEXT DEFAULT 'not_started', -- not_started | in_progress | completed
  completed_at TIMESTAMP,
  duration_minutes INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_student_lessons_student ON student_lessons(student_id);
CREATE INDEX idx_student_lessons_lesson ON student_lessons(lesson_id);

CREATE TABLE IF NOT EXISTS student_labs (
  id TEXT PRIMARY KEY,
  student_id TEXT REFERENCES students(id),
  lab_id TEXT REFERENCES labs(id),
  submission_text TEXT,
  submission_url TEXT,  -- GitHub, etc
  status TEXT DEFAULT 'not_started', -- not_started | submitted | graded | passed | failed
  score INTEGER,  -- 0-100
  feedback TEXT,
  submitted_at TIMESTAMP,
  graded_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_student_labs_student ON student_labs(student_id);
CREATE INDEX idx_student_labs_lab ON student_labs(lab_id);
CREATE INDEX idx_student_labs_status ON student_labs(status);

CREATE TABLE IF NOT EXISTS student_assessments (
  id TEXT PRIMARY KEY,
  student_id TEXT REFERENCES students(id),
  assessment_id TEXT REFERENCES assessments(id),
  submission TEXT,
  score INTEGER,  -- 0-100
  passed BOOLEAN,
  submitted_at TIMESTAMP,
  graded_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_student_assessments_student ON student_assessments(student_id);
CREATE INDEX idx_student_assessments_assessment ON student_assessments(assessment_id);

-- ─────────────────────────────────────────────────────────────
-- Capstone Project
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS capstones (
  id TEXT PRIMARY KEY,
  student_id TEXT REFERENCES students(id),
  title TEXT,
  description TEXT,
  status TEXT DEFAULT 'in_progress', -- in_progress | submitted | under_review | approved | needs_revision | failed
  submission_url TEXT,  -- GitHub repo
  submitted_at TIMESTAMP,
  reviewed_at TIMESTAMP,
  approved_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_capstones_student ON capstones(student_id);
CREATE INDEX idx_capstones_status ON capstones(status);

CREATE TABLE IF NOT EXISTS capstone_artifacts (
  id TEXT PRIMARY KEY,
  capstone_id TEXT REFERENCES capstones(id),
  artifact_type TEXT NOT NULL, -- architecture | code | dpia | risk_register | etc
  title TEXT,
  content TEXT,  -- JSON or reference
  status TEXT DEFAULT 'pending', -- pending | approved | needs_revision | rejected
  feedback TEXT,
  reviewed_by TEXT,
  reviewed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_capstone_artifacts_capstone ON capstone_artifacts(capstone_id);
CREATE INDEX idx_capstone_artifacts_type ON capstone_artifacts(artifact_type);

-- ─────────────────────────────────────────────────────────────
-- Legal & Regulatory Sources (Versioned)
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS legal_sources (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  jurisdiction TEXT,  -- Chile | EU | International | etc
  source_type TEXT,  -- law | regulation | framework | standard | guideline
  official_url TEXT,
  version TEXT,
  effective_date DATE,
  valid_until DATE,
  summary TEXT,
  topics TEXT,  -- JSON array
  last_verified DATE,
  verified_by TEXT,
  deprecated_reason TEXT,
  deprecated_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_legal_sources_jurisdiction ON legal_sources(jurisdiction);
CREATE INDEX idx_legal_sources_type ON legal_sources(source_type);

-- ─────────────────────────────────────────────────────────────
-- Content Review & Approval Workflow
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS content_reviews (
  id TEXT PRIMARY KEY,
  content_id TEXT NOT NULL,  -- lesson_id | lab_id | etc
  content_type TEXT NOT NULL, -- lesson | lab | assessment | capstone_artifact
  reviewer_id TEXT,
  review_type TEXT NOT NULL, -- expert | legal | compliance
  status TEXT DEFAULT 'pending', -- pending | approved | needs_revision | rejected
  comments TEXT,
  reviewed_at TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_content_reviews_content ON content_reviews(content_id);
CREATE INDEX idx_content_reviews_status ON content_reviews(status);
CREATE INDEX idx_content_reviews_type ON content_reviews(review_type);

-- ─────────────────────────────────────────────────────────────
-- Badges & Certificates
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS badges (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  domain TEXT,  -- enterprise_architecture | data_governance | etc
  criteria TEXT,  -- JSON: conditions to earn badge
  icon_url TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS student_badges (
  id TEXT PRIMARY KEY,
  student_id TEXT REFERENCES students(id),
  badge_id TEXT REFERENCES badges(id),
  earned_at TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_student_badges_student ON student_badges(student_id);

-- ─────────────────────────────────────────────────────────────
-- Audit Trail (All Changes)
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS audit_log (
  id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,  -- lesson | lab | assessment | student | etc
  entity_id TEXT NOT NULL,
  action TEXT NOT NULL,  -- create | update | approve | reject | publish | delete
  changed_by TEXT,
  changes TEXT,  -- JSON diff
  timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);

-- ─────────────────────────────────────────────────────────────
-- Initialization: Insert sample program
-- ─────────────────────────────────────────────────────────────

INSERT INTO programs (id, official_name, slug, duration_months, recommended_hours)
VALUES (
  'aif369-master-001',
  'AIF369 Master en Arquitectura, Gobernanza de Datos e Inteligencia Artificial',
  'master-arquitectura-gobernanza-datos',
  12,
  420
)
ON CONFLICT DO NOTHING;
