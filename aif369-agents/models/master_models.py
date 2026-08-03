"""Pydantic models for AIF369 Master Program in Data & AI Governance

These models match the structure in aif369_master_data_ai_governance.json
Used for validation, serialization, and API contracts.
"""
from typing import Optional, List
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class ProgramType(str, Enum):
    """Program types - always program_type = programa_profesional_privado"""
    PROFESSIONAL = "programa_profesional_privado"


class ContentStatus(str, Enum):
    """Content lifecycle statuses"""
    DRAFT = "draft"
    EXPERT_REVIEW = "expert_review"
    LEGAL_REVIEW = "legal_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


class CompetencyDomain(BaseModel):
    """Competency domain (e.g., Enterprise Architecture, Data Governance)"""
    id: str
    name: str
    frameworks: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    platforms: Optional[List[str]] = None
    tools: Optional[List[str]] = None


class LearningOutcome(BaseModel):
    """Learning outcome for the program"""
    text: str = Field(..., description="Learning outcome description")
    domain_id: Optional[str] = None


class Module(BaseModel):
    """Module within a month"""
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    learning_objectives: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    frameworks: Optional[List[str]] = None


class Month(BaseModel):
    """Curriculum month"""
    id: Optional[str] = None
    month: int = Field(..., ge=1, le=12)
    title: str
    certification_alignment: Optional[List[str]] = None
    modules: List[str] = Field(default_factory=list, description="Module titles")
    deliverables: List[str] = Field(default_factory=list)
    rights_of_data_subjects: Optional[List[str]] = None


class ProgramInfo(BaseModel):
    """Program metadata"""
    id: str
    slug: str
    brand: str
    official_name: str
    short_name: str
    program_type: ProgramType
    academic_disclaimer: str
    positioning: str
    duration_months: int = 12
    recommended_hours: int = 420
    delivery_mode: List[str]
    audience: List[str]


class EntryRequirements(BaseModel):
    """Entry requirements"""
    required: List[str] = Field(default_factory=list)
    recommended: List[str] = Field(default_factory=list)


class GraduateProfile(BaseModel):
    """Graduate profile / exit competencies"""
    summary: str
    target_roles: List[str]


class CapstoneAgent(BaseModel):
    """Agent required for capstone"""
    name: str
    description: Optional[str] = None


class CapstoneRAGComponent(BaseModel):
    """RAG component required for capstone"""
    name: str
    purpose: str
    required_features: Optional[List[str]] = None


class Capstone(BaseModel):
    """Capstone project specification"""
    id: Optional[str] = None
    name: str
    business_context: str
    business_capabilities: List[str]
    architecture_scope: List[str]
    required_agents: Optional[List[str]] = None
    required_rag_components: Optional[List[str]] = None
    mandatory_artifacts: List[str]
    acceptance_criteria: List[str]


class AssessmentModel(BaseModel):
    """Assessment weighting and criteria"""
    weights_percent: dict = Field(default_factory=dict, description="Component: weight %")
    passing_score: int = 70
    requirements: List[str] = Field(default_factory=list)
    badges: List[str] = Field(default_factory=list)


class Curriculum(BaseModel):
    """Curriculum structure"""
    structure: str
    months: List[Month]


class Program(BaseModel):
    """Full AIF369 Master Program"""
    schema_version: str = "1.0.0"
    content_language: str = "es-CL"

    program: ProgramInfo
    learning_outcomes: List[str]
    competency_domains: List[CompetencyDomain]
    curriculum: Curriculum
    entry_requirements: EntryRequirements
    graduate_profile: GraduateProfile
    capstone: Capstone
    assessment_model: AssessmentModel


# ─────────────────────────────────────────────────────────────
# Content model for lessons, labs, assessments
# ─────────────────────────────────────────────────────────────

class ContentSection(BaseModel):
    """Section within lesson content"""
    title: str
    content: str
    examples: Optional[List[str]] = None


class KnowledgeCheck(BaseModel):
    """Knowledge check question"""
    id: Optional[str] = None
    question: str
    options: List[str]
    correct_answer: int = Field(..., ge=0, description="Index of correct option")
    explanation: Optional[str] = None


class Activity(BaseModel):
    """Activity or exercise within a lesson"""
    title: str
    description: str
    estimated_minutes: int
    requirements: Optional[List[str]] = None
    deliverable: Optional[str] = None


class Lesson(BaseModel):
    """Individual lesson"""
    id: str
    month: int
    module_title: str
    title: str
    summary: str
    learning_objectives: List[str]
    prerequisites: Optional[List[str]] = None
    estimated_minutes: int
    content_sections: List[ContentSection]
    examples: List[str] = Field(default_factory=list)
    activity: Optional[Activity] = None
    knowledge_check: Optional[List[KnowledgeCheck]] = None
    references: List[str] = Field(default_factory=list)

    # Metadata
    status: ContentStatus = ContentStatus.DRAFT
    last_reviewed_at: Optional[datetime] = None
    requires_legal_review: bool = False
    tags: List[str] = Field(default_factory=list)


class Lab(BaseModel):
    """Laboratory exercise"""
    id: str
    month: int
    title: str
    description: str
    learning_objectives: List[str]
    estimated_hours: float
    prerequisites: List[str] = Field(default_factory=list)

    # Instructions
    setup_instructions: str
    steps: List[str]
    validation_criteria: List[str]

    # Resources
    starter_code: Optional[str] = None  # URL or embedded
    solution: Optional[str] = None
    tools_required: List[str] = Field(default_factory=list)

    status: ContentStatus = ContentStatus.DRAFT


class Assessment(BaseModel):
    """Evaluation/Assessment"""
    id: str
    month: int
    title: str
    type: str = Field(..., description="e.g., quiz, case_study, artifact_review")
    description: str
    estimated_minutes: int
    questions: Optional[List[KnowledgeCheck]] = None
    rubric: Optional[dict] = None  # Criterion: weight & description
    passing_score: int = 70


class Template(BaseModel):
    """Template for architecture or documentation"""
    id: str
    title: str
    description: str
    category: str  # e.g., "TOGAF", "C4", "DPIA"
    file_format: str  # e.g., "drawio", "md", "xlsx"
    download_url: str
    use_case: str
    example_output: Optional[str] = None


class LegalSource(BaseModel):
    """Reference to legal or regulatory source"""
    id: str
    title: str
    jurisdiction: str  # e.g., "Chile", "EU", "International"
    source_type: str  # e.g., "law", "regulation", "framework", "standard"
    url: str
    effective_date: str
    last_updated: str
    version: str
    summary: str
    topics: List[str]


class AdminPanel(BaseModel):
    """Admin panel content management"""
    lesson: Optional[Lesson] = None
    lab: Optional[Lab] = None
    assessment: Optional[Assessment] = None
    template: Optional[Template] = None
    legal_source: Optional[LegalSource] = None
