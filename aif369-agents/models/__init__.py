"""Models package"""
import sys

# Import with graceful fallback for testing environments
try:
    from .enums import AgentType, TaskStatus, ToolType
except ImportError:
    AgentType = TaskStatus = ToolType = None

try:
    from .task import Task
except ImportError:
    Task = None

try:
    from .result import Result
except ImportError:
    Result = None

__all__ = ["AgentType", "TaskStatus", "ToolType", "Task", "Result"]
