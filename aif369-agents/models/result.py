"""Result data model"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from .enums import TaskStatus


@dataclass
class Result:
    """
    Immutable result representation
    Single Responsibility: Hold result data only
    """
    task_id: str
    status: TaskStatus
    output: Any
    created_at: datetime = field(default_factory=datetime.utcnow)
    execution_time_ms: float = 0.0
    error: Optional[str] = None
    agent_used: Optional[str] = None
    tokens_used: int = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "output": self.output,
            "created_at": self.created_at.isoformat(),
            "execution_time_ms": self.execution_time_ms,
            "error": self.error,
            "agent_used": self.agent_used,
            "tokens_used": self.tokens_used,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Result":
        """Reconstruct from dictionary"""
        return cls(
            task_id=data["task_id"],
            status=TaskStatus(data["status"]),
            output=data["output"],
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
            execution_time_ms=data.get("execution_time_ms", 0.0),
            error=data.get("error"),
            agent_used=data.get("agent_used"),
            tokens_used=data.get("tokens_used", 0),
            metadata=data.get("metadata", {}),
        )

    @property
    def is_success(self) -> bool:
        """Check if execution was successful"""
        return self.status == TaskStatus.COMPLETED and self.error is None

    @property
    def is_failure(self) -> bool:
        """Check if execution failed"""
        return self.status in (TaskStatus.FAILED, TaskStatus.TIMEOUT)
