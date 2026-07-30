"""Agent factory (Factory pattern)"""
from typing import Optional, Union
from models import AgentType
from agents.base import BaseAgent
from agents.v1_agent import V1Agent
from agents.v2_agent import V2Agent
from agents.ventas_agent import VentasAgent
from agents.caio_agent import CAIOAgent
from agents.damabook_agent import DamabookAgent
from core import LoggerManager


class AgentFactory:
    """
    Factory Pattern: Create agents without exposing implementation

    Single Responsibility: Agent creation only
    Dependency Injection: LoggerManager injected

    Supported agents:
    - v1_mistral: V1Agent (ReAct)
    - v2_llama: V2Agent (LangGraph)
    - ventas: VentasAgent (Sales specialist)
    - caio: CAIOAgent (Consulting specialist)

    Usage:
        agent = AgentFactory.create("v1_mistral")
        agent = AgentFactory.create(AgentType.V1_MISTRAL)
        agent = AgentFactory.create("ventas")
    """

    _instances: dict = {}
    logger = LoggerManager.get_logger("AgentFactory")

    # Type mapping
    TYPE_MAP = {
        "v1_mistral": ("v1_mistral", V1Agent),
        "v2_llama": ("v2_llama", V2Agent),
        "ventas": ("ventas", VentasAgent),
        "caio": ("caio", CAIOAgent),
        "damabook": ("damabook", DamabookAgent),
        AgentType.V1_MISTRAL: ("v1_mistral", V1Agent),
        AgentType.V2_LLAMA: ("v2_llama", V2Agent),
    }

    @staticmethod
    def create(agent_type: Union[str, AgentType]) -> BaseAgent:
        """
        Create agent instance (lazy instantiation)

        Args:
            agent_type: AgentType enum or string ("v1_mistral", "ventas", etc)

        Returns:
            BaseAgent instance

        Raises:
            ValueError: if agent_type not recognized
        """
        # Normalize to string key
        if isinstance(agent_type, AgentType):
            key = agent_type.value
        else:
            key = agent_type

        # Singleton pattern for agents (reuse instances)
        if key in AgentFactory._instances:
            return AgentFactory._instances[key]

        # Create new agent
        if key in AgentFactory.TYPE_MAP:
            _, agent_class = AgentFactory.TYPE_MAP[key]
            agent = agent_class()
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

        AgentFactory._instances[key] = agent
        AgentFactory.logger.info(f"Created agent: {agent}")

        return agent

    @staticmethod
    def get_agent(agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID if already created"""
        return AgentFactory._instances.get(agent_id)

    @staticmethod
    def get_all_agents() -> dict:
        """Get all created agent instances"""
        return AgentFactory._instances.copy()

    @staticmethod
    def list_available() -> dict:
        """List all available agent types"""
        return {
            "v1_mistral": "ReAct agent (Mistral 7B)",
            "v2_llama": "LangGraph agent (Llama 70B)",
            "ventas": "Sales specialist (Courses & products)",
            "caio": "Consulting specialist (Enterprise AI)",
            "damabook": "Data Governance expert (Ley 21.719 compliance)",
        }

    @staticmethod
    def reset():
        """Reset factory (for testing)"""
        AgentFactory._instances.clear()
        AgentFactory.logger.warning("Factory reset")
