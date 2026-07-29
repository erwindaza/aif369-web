"""Base configuration manager (Singleton pattern)"""
import os
from typing import Optional
from dotenv import load_dotenv


class ConfigManager:
    """
    Singleton: manages all configuration
    Thread-safe lazy initialization
    """
    _instance: Optional["ConfigManager"] = None
    _initialized: bool = False

    def __new__(cls) -> "ConfigManager":
        """Singleton pattern - ensure only one instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize only once"""
        if self._initialized:
            return

        load_dotenv()

        # Ollama settings
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.mistral_model = os.getenv("MISTRAL_MODEL", "mistral:7b")
        self.llama_model = os.getenv("LLAMA_MODEL", "llama2:70b")

        # Agent settings
        self.agent_v1_port = int(os.getenv("AGENT_V1_PORT", "8001"))
        self.agent_v2_port = int(os.getenv("AGENT_V2_PORT", "8002"))
        self.orchestrator_port = int(os.getenv("ORCHESTRATOR_PORT", "8000"))

        # Timing
        self.default_timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", "30"))
        self.queue_poll_interval_ms = int(os.getenv("QUEUE_POLL_INTERVAL", "100"))

        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.debug_mode = os.getenv("DEBUG", "false").lower() == "true"

        # Environment
        self.environment = os.getenv("ENVIRONMENT", "development")

        ConfigManager._initialized = True

    @staticmethod
    def get_instance() -> "ConfigManager":
        """Get singleton instance"""
        if ConfigManager._instance is None:
            ConfigManager()
        return ConfigManager._instance

    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"

    def __repr__(self) -> str:
        return (
            f"<ConfigManager "
            f"ollama={self.ollama_host} "
            f"env={self.environment}>"
        )
