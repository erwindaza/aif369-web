"""Base agent (Abstract class - Open/Closed Principle)"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List
import time
from models import Task, Result, TaskStatus
from core import LoggerManager


class BaseAgent(ABC):
    """
    Abstract base class for all agents

    SOLID Principles:
    - S: Single responsibility (execute tasks)
    - O: Open for extension (subclasses implement specific logic)
    - L: Liskov substitution (V1Agent, V2Agent interchangeable)
    - D: Dependency injection (logger, config injected)

    Template Method Pattern:
    - execute() defines overall flow
    - Subclasses implement specific steps
    """

    def __init__(self, agent_id: str, model_name: str):
        """
        Initialize agent with dependency injection

        Args:
            agent_id: unique identifier (v1, v2, etc)
            model_name: LLM model name (mistral:7b, llama2:70b)
        """
        self.agent_id = agent_id
        self.model_name = model_name
        self.logger = LoggerManager.get_logger(f"Agent[{agent_id}]")
        self._execution_count = 0
        self._total_execution_time = 0.0

    async def execute(self, task: Task) -> Result:
        """
        Execute task (Template Method Pattern)
        Main flow: validate → process → format → return
        """
        start_time = time.time()

        try:
            # 1. Validate task
            await self._validate_task(task)

            # 2. Process (subclass implements)
            output = await self._process(task)

            # 3. Format result
            execution_time = (time.time() - start_time) * 1000  # ms

            result = Result(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                output=output,
                execution_time_ms=execution_time,
                agent_used=self.agent_id,
                tokens_used=await self._estimate_tokens(output),
            )

            self._update_stats(execution_time)

            self.logger.info(
                f"Task {task.task_id} completed in {execution_time:.0f}ms"
            )

            return result

        except asyncio.TimeoutError:
            self.logger.error(f"Task {task.task_id} timeout")
            return Result(
                task_id=task.task_id,
                status=TaskStatus.TIMEOUT,
                output=None,
                error="Execution timeout",
                agent_used=self.agent_id,
            )

        except Exception as e:
            self.logger.error(f"Task {task.task_id} failed: {e}")
            return Result(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                output=None,
                error=str(e),
                agent_used=self.agent_id,
            )

    @abstractmethod
    async def _process(self, task: Task) -> Any:
        """
        Subclasses implement actual processing logic

        Args:
            task: Task to process

        Returns:
            processed output
        """
        pass

    async def _validate_task(self, task: Task) -> None:
        """Validate task structure (Interface Segregation)"""
        if not task.task_id:
            raise ValueError("Task ID required")
        if not task.payload:
            raise ValueError("Task payload required")

    async def _estimate_tokens(self, output: Any) -> int:
        """Estimate tokens in output (rough approximation)"""
        if isinstance(output, str):
            return len(output.split()) // 4  # ~4 chars per token
        elif isinstance(output, dict):
            return len(str(output).split()) // 4
        return 0

    def _update_stats(self, execution_time_ms: float) -> None:
        """Update agent statistics"""
        self._execution_count += 1
        self._total_execution_time += execution_time_ms

    async def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        avg_time = (
            self._total_execution_time / self._execution_count
            if self._execution_count > 0
            else 0
        )

        return {
            "agent_id": self.agent_id,
            "model": self.model_name,
            "execution_count": self._execution_count,
            "average_execution_time_ms": avg_time,
            "total_execution_time_ms": self._total_execution_time,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.agent_id} model={self.model_name}>"


# Fix missing import
import asyncio
