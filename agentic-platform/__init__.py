"""
AIF369 Agentic Platform
Multi-agent sales discovery and proposal generation system
"""

from .orchestrator import AgentOrchestrator, orchestrator
from .config import PlatformState

__all__ = ["AgentOrchestrator", "orchestrator", "PlatformState"]
