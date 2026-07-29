"""Scheduler manager for recurring tasks (Singleton pattern)"""
import asyncio
from typing import Optional, Callable, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from core.logger import LoggerManager


class SchedulerManager:
    """
    Singleton: manages all recurring tasks
    - Single Responsibility: scheduling only
    - Dependency Injection: logger injected
    - Uses APScheduler for robustness

    Example:
        scheduler = SchedulerManager.get_instance()
        await scheduler.add_task(
            "enrich_products_hourly",
            "0 * * * *",  # Every hour
            my_async_function,
            my_arg1, my_arg2
        )
    """
    _instance: Optional["SchedulerManager"] = None

    def __new__(cls) -> "SchedulerManager":
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize scheduler"""
        self.logger = LoggerManager.get_logger("SchedulerManager")
        self.scheduler = AsyncIOScheduler()
        self._tasks: dict = {}

    async def start(self):
        """Start scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info("SchedulerManager started")

    async def stop(self):
        """Stop scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("SchedulerManager stopped")

    async def add_task(
        self,
        task_name: str,
        cron_expression: str,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> str:
        """
        Add recurring task using cron expression

        Args:
            task_name: unique task identifier
            cron_expression: cron format string (e.g., "0 * * * *" = hourly)
            func: async function to execute
            *args, **kwargs: function arguments

        Returns:
            task_id

        Examples:
            "0 * * * *"     → every hour
            "0 */6 * * *"   → every 6 hours
            "0 0 * * 0"     → weekly (Sunday)
            "0 0 1 * *"     → monthly (1st day)
        """
        try:
            self.scheduler.add_job(
                func,
                trigger=CronTrigger.from_crontab(cron_expression),
                args=args,
                kwargs=kwargs,
                id=task_name,
                name=task_name,
                replace_existing=True,
            )

            self._tasks[task_name] = {
                "cron": cron_expression,
                "function": func.__name__,
            }

            self.logger.info(
                f"Task '{task_name}' scheduled: {cron_expression}"
            )

            return task_name

        except Exception as e:
            self.logger.error(f"Failed to schedule task '{task_name}': {e}")
            raise

    async def remove_task(self, task_name: str) -> bool:
        """Remove scheduled task"""
        try:
            self.scheduler.remove_job(task_name)
            del self._tasks[task_name]
            self.logger.info(f"Task '{task_name}' removed")
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove task '{task_name}': {e}")
            return False

    async def list_tasks(self) -> dict:
        """List all scheduled tasks"""
        return self._tasks.copy()

    @staticmethod
    def get_instance() -> "SchedulerManager":
        """Get singleton instance"""
        if SchedulerManager._instance is None:
            SchedulerManager()
        return SchedulerManager._instance

    def __repr__(self) -> str:
        return f"<SchedulerManager tasks={len(self._tasks)}>"
