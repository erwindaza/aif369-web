"""Main orchestrator - coordinates V1 and V2 agents"""
import asyncio
from typing import Optional, List
from models import Task, Result, AgentType, TaskStatus
from agents import AgentFactory
from core import QueueManager, SchedulerManager, LoggerManager


class Orchestrator:
    """
    Orchestrator: Coordinates V1 and V2 agents

    Responsibilities:
    - Route tasks to appropriate agents
    - Manage execution flow
    - Compare results
    - Coordinate scheduling

    Single Responsibility: Coordination only
    Dependency Injection: All managers injected
    """

    def __init__(self):
        self.logger = LoggerManager.get_logger("Orchestrator")
        self.queue_manager = QueueManager.get_instance()
        self.scheduler_manager = SchedulerManager.get_instance()

        # Initialize agents (lazy)
        self.agent_v1 = None
        self.agent_v2 = None

    async def initialize(self):
        """Initialize agents and start scheduler"""
        self.agent_v1 = AgentFactory.create(AgentType.V1_MISTRAL)
        self.agent_v2 = AgentFactory.create(AgentType.V2_LLAMA)

        # Start scheduler for recurring tasks
        await self.scheduler_manager.start()

        self.logger.info("Orchestrator initialized with V1 and V2 agents")

    async def submit_task(self, task: Task) -> str:
        """
        Submit task to queue

        Args:
            task: Task to execute

        Returns:
            task_id

        Latency: <10ms (async queue operation)
        """
        task_id = await self.queue_manager.enqueue_task(task)
        self.logger.info(f"Task {task_id} submitted ({task.agent_type.value})")
        return task_id

    async def process_tasks(self):
        """
        Main event loop: process tasks from queues

        This runs continuously, pulling tasks and executing them
        """
        self.logger.info("Starting task processor")

        try:
            while True:
                # Check V1 queue
                v1_task = await self.queue_manager.dequeue_task("v1_mistral")
                if v1_task:
                    asyncio.create_task(self._execute_task(v1_task, self.agent_v1))

                # Check V2 queue
                v2_task = await self.queue_manager.dequeue_task("v2_llama")
                if v2_task:
                    asyncio.create_task(self._execute_task(v2_task, self.agent_v2))

                # Small sleep to prevent busy-waiting
                await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            self.logger.info("Task processor stopped")
        except Exception as e:
            self.logger.error(f"Task processor error: {e}")
            raise

    async def _execute_task(self, task: Task, agent) -> None:
        """Execute task and store result"""
        try:
            result = await agent.execute(task)
            await self.queue_manager.store_result(result)
        except Exception as e:
            self.logger.error(f"Task execution error: {e}")

    async def submit_and_wait(
        self, task: Task, timeout_seconds: Optional[int] = None
    ) -> Result:
        """
        Submit task and wait for result

        Args:
            task: Task to execute
            timeout_seconds: max wait time (uses task.timeout_seconds if None)

        Returns:
            Result

        Note: This is blocking. For non-blocking, use submit_task()
        """
        timeout = timeout_seconds or task.timeout_seconds

        task_id = await self.submit_task(task)
        result = await self.queue_manager.get_result(task_id, timeout_seconds=timeout)

        if result is None:
            result = Result(
                task_id=task_id,
                status=TaskStatus.TIMEOUT,
                output=None,
                error=f"Timeout after {timeout}s",
            )

        return result

    async def run_recurring_task(
        self, task_name: str, cron_expr: str, agent_type: AgentType, payload: dict
    ) -> str:
        """
        Schedule recurring task

        Example:
            await orchestrator.run_recurring_task(
                "enrich_new_products",
                "0 * * * *",  # Every hour
                AgentType.V2_LLAMA,
                {"query": "new_products"}
            )
        """
        async def task_func():
            task = Task(
                task_id=f"{task_name}_{int(__import__('time').time())}",
                agent_type=agent_type,
                payload=payload,
            )
            await self.submit_task(task)

        task_id = await self.scheduler_manager.add_task(
            task_name, cron_expr, task_func
        )

        self.logger.info(f"Recurring task '{task_name}' scheduled")

        return task_id

    async def get_system_stats(self) -> dict:
        """Get system statistics"""
        queue_stats = await self.queue_manager.get_queue_stats()

        v1_stats = await self.agent_v1.get_stats() if self.agent_v1 else {}
        v2_stats = await self.agent_v2.get_stats() if self.agent_v2 else {}

        scheduled_tasks = await self.scheduler_manager.list_tasks()

        return {
            "queue": queue_stats,
            "agents": {
                "v1": v1_stats,
                "v2": v2_stats,
            },
            "scheduled_tasks": scheduled_tasks,
        }

    async def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Shutting down orchestrator")
        await self.scheduler_manager.stop()
        self.logger.info("Orchestrator shutdown complete")

    def __repr__(self) -> str:
        return "<Orchestrator v1+v2 agents>"
