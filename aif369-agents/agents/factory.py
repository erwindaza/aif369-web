"""Agent factory (Factory pattern)"""
from typing import Optional
from models import AgentType
from agents.base import BaseAgent
from agents.v1_agent import V1Agent
from agents.v2_agent import V2Agent
from core import LoggerManager


class AgentFactory:
    """
    Factory Pattern: Create agents without exposing implementation

    Single Responsibility: Agent creation only
    Dependency Injection: LoggerManager injected

    Usage:
        agent = AgentFactory.create(AgentType.V1_MISTRAL)
        agent = AgentFactory.create(AgentType.V2_LLAMA)
    """

    _instances: dict = {}
    logger = LoggerManager.get_logger("AgentFactory")

    @staticmethod
    def create(agent_type: AgentType) -> BaseAgent:
        """
        Create agent instance (lazy instantiation)

        Args:
            agent_type: AgentType enum value

        Returns:
            BaseAgent instance (V1Agent or V2Agent)

        Raises:
            ValueError: if agent_type not recognized
        """
        # Singleton pattern for agents (reuse instances)
        if agent_type in AgentFactory._instances:
            return AgentFactory._instances[agent_type]

        if agent_type == AgentType.V1_MISTRAL:
            agent = V1Agent()
        elif agent_type == AgentType.V2_LLAMA:
            agent = V2Agent()
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

        AgentFactory._instances[agent_type] = agent
        AgentFactory.logger.info(f"Created agent: {agent}")

        return agent

    @staticmethod
    def get_all_agents() -> dict:
        """Get all created agent instances"""
        return AgentFactory._instances.copy()

    @staticmethod
    def reset():
        """Reset factory (for testing)"""
        AgentFactory._instances.clear()
        AgentFactory.logger.warning("Factory reset")
