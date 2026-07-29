"""Centralized logger (Singleton pattern)"""
import logging
import sys
from typing import Optional
from config.base import ConfigManager


class LoggerManager:
    """
    Singleton: centralized logging for entire system
    Single Responsibility: manage logging configuration
    """
    _instance: Optional["LoggerManager"] = None
    _loggers: dict = {}

    def __new__(cls) -> "LoggerManager":
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_logging()
        return cls._instance

    def _setup_logging(self):
        """Setup logging configuration"""
        config = ConfigManager.get_instance()

        # Root logger
        logging.basicConfig(
            level=config.log_level,
            format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
            ]
        )

        # Reduce noise from third-party libraries
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get or create logger for module"""
        if name not in LoggerManager._loggers:
            LoggerManager._loggers[name] = logging.getLogger(name)
        return LoggerManager._loggers[name]

    @staticmethod
    def get_instance() -> "LoggerManager":
        """Get singleton instance"""
        if LoggerManager._instance is None:
            LoggerManager()
        return LoggerManager._instance
