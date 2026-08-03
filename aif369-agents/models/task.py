"""Task data model"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from .enums import AgentType, TaskStatus


@dataclass
class Task:
    """
    Immutable task representation
    Single Responsibility: Hold task data only
    """
    task_id: str
    agent_type: AgentType
    payload: dict
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: TaskStatus = TaskStatus.QUEUED
    priority: int = 1
    timeout_seconds: int = 30
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary (for queue storage)"""
        return {
            "task_id": self.task_id,
            "agent_type": self.agent_type.value,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "priority": self.priority,
            "timeout_seconds": self.timeout_seconds,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Reconstruct from dictionary"""
        return cls(
            task_id=data["task_id"],
            agent_type=AgentType(data["agent_type"]),
            payload=data["payload"],
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
            status=TaskStatus(data.get("status", "queued")),
            priority=data.get("priority", 1),
            timeout_seconds=data.get("timeout_seconds", 30),
            metadata=data.get("metadata", {}),
        )
