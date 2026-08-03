"""Agents package"""
# Import with graceful fallback for testing environments
try:
    from .base import BaseAgent
except ImportError:
    BaseAgent = None

try:
    from .v1_agent import V1Agent
except ImportError:
    V1Agent = None

try:
    from .v2_agent import V2Agent
except ImportError:
    V2Agent = None

# Business agents
try:
    from .ventas_agent import VentasAgent
except ImportError:
    VentasAgent = None

try:
    from .caio_agent import CAIOAgent
except ImportError:
    CAIOAgent = None

try:
    from .damabook_agent import DamabookAgent
except ImportError:
    DamabookAgent = None

# Master program agents
try:
    from .instructor_agent import InstructorAgent
except ImportError:
    InstructorAgent = None

try:
    from .evaluator_agent import EvaluatorAgent
except ImportError:
    EvaluatorAgent = None

try:
    from .compliance_agent import ComplianceAgent
except ImportError:
    ComplianceAgent = None

try:
    from .factory import AgentFactory
except ImportError:
    AgentFactory = None

__all__ = [
    "BaseAgent",
    "V1Agent",
    "V2Agent",
    "VentasAgent",
    "CAIOAgent",
    "DamabookAgent",
    "InstructorAgent",
    "EvaluatorAgent",
    "ComplianceAgent",
    "AgentFactory",
]
