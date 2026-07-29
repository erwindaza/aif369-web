"""Base tool class (Abstract - Strategy pattern)"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from core import LoggerManager


class BaseTool(ABC):
    """
    Abstract base class for all tools

    Strategy Pattern: Different tool implementations
    Single Responsibility: Each tool does ONE thing
    Dependency Injection: logger injected

    Tools are functions agents can call during execution.
    Examples:
      - WhatsAppTool: send messages to customers
      - SearchTool: search database
      - ValidationTool: validate data
      - InterAgentTool: trigger events for other agents
    """

    def __init__(self, tool_name: str):
        """
        Initialize tool

        Args:
            tool_name: unique identifier (whatsapp, search, validate, etc)
        """
        self.tool_name = tool_name
        self.logger = LoggerManager.get_logger(f"Tool[{tool_name}]")
        self._execution_count = 0
        self._total_execution_time = 0.0

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        Execute tool action

        Subclasses implement specific logic

        Returns:
            Tool output (any type)

        Raises:
            ToolExecutionError: if execution fails
        """
        pass

    async def validate_inputs(self, **kwargs) -> bool:
        """
        Validate tool inputs before execution

        Override in subclasses for specific validation

        Returns:
            True if valid, False otherwise
        """
        return True

    async def get_stats(self) -> Dict[str, Any]:
        """Get tool execution statistics"""
        avg_time = (
            self._total_execution_time / self._execution_count
            if self._execution_count > 0
            else 0
        )

        return {
            "tool_name": self.tool_name,
            "execution_count": self._execution_count,
            "average_execution_time_ms": avg_time,
            "total_execution_time_ms": self._total_execution_time,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.tool_name}>"
