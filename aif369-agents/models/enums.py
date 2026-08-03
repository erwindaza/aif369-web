"""Enums for agent system"""
from enum import Enum


class AgentType(str, Enum):
    """Agent types"""
    V1_MISTRAL = "v1_mistral"
    V2_LLAMA = "v2_llama"


class TaskStatus(str, Enum):
    """Task execution status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ToolType(str, Enum):
    """Tool types"""
    SEARCH = "search"
    VALIDATION = "validation"
    ENRICHMENT = "enrichment"
    EXTRACTION = "extraction"
