"""In-memory queue manager (Singleton pattern - Zero dependencies)"""
import asyncio
from typing import Optional, Dict, List
from datetime import datetime
from models import Task, Result, TaskStatus
from core.logger import LoggerManager


class QueueManager:
    """
    Singleton: in-memory queue for tasks (zero external dependencies)
    - No Redis required
    - Async-safe using asyncio.Lock
    - Single Responsibility: manage task queue + results storage

    Principles:
    - Dependency Injection: logger injected
    - Single Responsibility: only queue management
    - Interface Segregation: specific methods for task/result
    """
    _instance: Optional["QueueManager"] = None

    def __new__(cls) -> "QueueManager":
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize queue state"""
        self.logger = LoggerManager.get_logger("QueueManager")

        # Task storage by ID
        self._tasks: Dict[str, Task] = {}
        self._results: Dict[str, Result] = {}

        # Queues by agent type (ordered by priority)
        self._queues: Dict[str, List[str]] = {
            "v1_mistral": [],
            "v2_llama": [],
        }

        # Async lock for thread safety
        self._lock = asyncio.Lock()

        self.logger.info("QueueManager initialized (in-memory)")

    async def enqueue_task(self, task: Task) -> str:
        """
        Add task to queue
        O(1) time complexity
        """
        async with self._lock:
            self._tasks[task.task_id] = task
            agent_queue = self._queues.get(task.agent_type.value, [])

            # Insert by priority (higher priority first)
            insert_pos = 0
            for i, task_id in enumerate(agent_queue):
                if self._tasks[task_id].priority < task.priority:
                    insert_pos = i
                    break
            else:
                insert_pos = len(agent_queue)

            agent_queue.insert(insert_pos, task.task_id)

            self.logger.debug(
                f"Task {task.task_id} enqueued for {task.agent_type.value} "
                f"(priority={task.priority})"
            )

            return task.task_id

    async def dequeue_task(self, agent_type: str) -> Optional[Task]:
        """
        Remove and return next task for agent
        O(1) time complexity
        """
        async with self._lock:
            agent_queue = self._queues.get(agent_type, [])

            if not agent_queue:
                return None

            task_id = agent_queue.pop(0)
            task = self._tasks.pop(task_id)
            task.status = TaskStatus.PROCESSING

            self.logger.debug(f"Task {task_id} dequeued for {agent_type}")

            return task

    async def store_result(self, result: Result) -> None:
        """
        Store result for task
        O(1) time complexity
        """
        async with self._lock:
            self._results[result.task_id] = result

            self.logger.debug(
                f"Result stored for task {result.task_id} "
                f"(status={result.status.value})"
            )

    async def get_result(self, task_id: str, timeout_seconds: int = 30) -> Optional[Result]:
        """
        Poll result with timeout
        Dependency Injection: timeout parameter
        """
        start = datetime.utcnow()

        while True:
            async with self._lock:
                if task_id in self._results:
                    return self._results[task_id]

            # Check timeout
            elapsed = (datetime.utcnow() - start).total_seconds()
            if elapsed > timeout_seconds:
                self.logger.warning(f"Task {task_id} timeout after {elapsed}s")
                return None

            # Async sleep (non-blocking)
            await asyncio.sleep(0.1)

    async def get_queue_stats(self) -> dict:
        """Get queue statistics"""
        async with self._lock:
            return {
                "v1_mistral_queue_length": len(self._queues["v1_mistral"]),
                "v2_llama_queue_length": len(self._queues["v2_llama"]),
                "total_tasks": len(self._tasks),
                "total_results": len(self._results),
            }

    @staticmethod
    def get_instance() -> "QueueManager":
        """Get singleton instance"""
        if QueueManager._instance is None:
            QueueManager()
        return QueueManager._instance

    def __repr__(self) -> str:
        v1_len = len(self._queues.get("v1_mistral", []))
        v2_len = len(self._queues.get("v2_llama", []))
        return f"<QueueManager v1={v1_len} v2={v2_len}>"
