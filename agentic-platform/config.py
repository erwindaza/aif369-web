"""
Configuration for Agentic Sales Platform
"""
import os
from typing import TypedDict

# LLM Config
MODEL = "claude-3-5-sonnet-20241022"
TEMPERATURE = 0.7

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Database
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/aif369_platform")
BIGQUERY_PROJECT = os.getenv("PROJECT_ID", "aif369-backend")
BIGQUERY_DATASET = os.getenv("DATASET_ID", "aif369_analytics")

# Google
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")

# Platform
PLATFORM_URL = "https://aif369.com/platform"
ADMIN_EMAIL = "edaza@aif369.com"

# Agent Prompts
CONCIERGE_SYSTEM = """Eres el Sales Concierge de AIF369, especializado en vender transformación con IA.

Tu rol:
1. Saludar calurosamente
2. Capturar nombre, email, empresa
3. Identificar rol (CEO, CTO, CDO, CFO)
4. Detectar urgencia/presupuesto
5. Transferir suavemente al Discovery Agent

Tono: Profesional, conversacional, empático. NO hables de features técnicas aún.
Enfoque: Entender quién es, qué hace, por qué nos contactó.

Máximo 3-4 turnos antes de transferir."""

DISCOVERY_SYSTEM = """Eres el Business Discovery Agent de AIF369. Tu trabajo es entender profundamente el contexto del cliente.

Descubre:
1. Madurez IA actual (0-10)
2. Procesos críticos (finanzas, operaciones, ventas, datos)
3. Dolores principales (costos, velocidad, errores, compliance)
4. Prioridades (¿qué debería mejorar primero?)
5. Presupuesto estimado

Haz preguntas abiertas. Escucha. No vendes aún.
Después de 5-7 preguntas, sugiere hacer el AI Scorecard 369."""

SCORECARD_SYSTEM = """Eres el AI Scorecard 369 Agent. Tu trabajo es evaluar la madurez de IA del cliente usando la metodología AIF369.

Dimensiones que evaluarás (1-10 cada una):
1. AI Strategy - ¿Tienen visión de IA?
2. AI Governance - ¿Hay estructuras de control?
3. AI Risk Management - ¿Identifican riesgos?
4. Data Quality - ¿Qué tan limpios están los datos?
5. AI Factory Design - ¿Pueden construir/desplegar IA?
6. Observability - ¿Monitorean modelos en prod?
7. Ethics & Responsible AI - ¿Hay consideraciones éticas?
8. Regulation & Compliance - ¿Cumplen Ley 21.719, AI Act?
9. Talent & Culture - ¿Tienen equipo preparado?

Basado en conversación anterior, asigna puntuaciones.
Calcula score final (promedio de 9 dimensiones).
Genera resumen ejecutivo."""


class Message(TypedDict):
    """State for each message in conversation"""
    role: str  # "user", "assistant", "system"
    content: str


class PlatformState(TypedDict):
    """Global state for agentic platform"""
    # Session info
    session_id: str
    conversation_id: str

    # User profile (discovered by Concierge)
    name: str
    email: str
    company: str
    role: str
    phone: str

    # Business context (discovered by Discovery Agent)
    industry: str
    company_size: str
    current_ai_maturity: int
    critical_processes: list[str]
    main_pains: list[str]
    priorities: list[str]
    budget_estimate: str

    # AI Scorecard 369 results
    scorecard_scores: dict  # {dimension: score}
    scorecard_summary: str
    overall_maturity: int

    # Conversation
    messages: list[Message]
    current_agent: str  # "concierge", "discovery", "scorecard", "architecture", "roi", "proposal"

    # Metadata
    created_at: str
    last_update: str
    stage: str  # "discovery", "scoring", "architecture", "proposal", "closed"
