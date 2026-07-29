"""Inter-Agent Communication Tool - Event-based agent coordination"""
import time
from typing import Dict, Any, Optional
from models import Task, AgentType
from tools.base import BaseTool


class InterAgentEventTool(BaseTool):
    """
    Inter-agent communication via events (NOT WhatsApp)

    Single Responsibility: Coordinate between agents
    Strategy Pattern: Different event types

    Internal Communication:
    - V1 can request detailed analysis from V2
    - V2 can trigger actions via V1
    - Event-based (async, non-blocking)

    Example:
        tool = InterAgentEventTool(queue_manager)
        await tool.execute(
            event_type="request_detailed_analysis",
            target_agent="v2_llama",
            data={"product_id": "123", ...}
        )
    """

    def __init__(self, queue_manager):
        super().__init__(tool_name="inter_agent")
        self.queue_manager = queue_manager

    async def validate_inputs(self, event_type: str, target_agent: str, **kwargs) -> bool:
        """Validate event parameters"""
        valid_events = [
            "request_detailed_analysis",
            "request_validation",
            "request_enrichment",
            "trigger_customer_notification",
        ]

        valid_agents = ["v1_mistral", "v2_llama"]

        if event_type not in valid_events:
            self.logger.warning(f"Invalid event type: {event_type}")
            return False

        if target_agent not in valid_agents:
            self.logger.warning(f"Invalid target agent: {target_agent}")
            return False

        return True

    async def execute(
        self,
        event_type: str,
        target_agent: str,
        data: Dict[str, Any],
        wait_for_result: bool = False,
        timeout_seconds: int = 30,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Send event to another agent

        Args:
            event_type: type of event (request_detailed_analysis, etc)
            target_agent: v1_mistral or v2_llama
            data: event data (passed to agent)
            wait_for_result: block until agent completes (optional)
            timeout_seconds: max wait time
            **kwargs: additional options

        Returns:
            {
                "status": "sent" | "failed" | "completed",
                "event_id": str,
                "target_agent": str,
                "result": {...} (if wait_for_result=True)
            }
        """
        start_time = time.time()

        # Validate
        if not await self.validate_inputs(event_type, target_agent):
            return {
                "status": "failed",
                "error": "Invalid event parameters",
            }

        try:
            # Create task for target agent
            event_task = Task(
                task_id=f"event_{event_type}_{int(time.time() * 1000)}",
                agent_type=AgentType(target_agent),
                payload={
                    "type": "inter_agent_event",
                    "event_type": event_type,
                    "data": data,
                    "source_agent": kwargs.get("source_agent", "unknown"),
                },
                priority=kwargs.get("priority", 2),  # Higher priority for events
                timeout_seconds=timeout_seconds,
            )

            # Enqueue task
            task_id = await self.queue_manager.enqueue_task(event_task)

            self.logger.info(
                f"Event '{event_type}' sent to {target_agent} "
                f"(task_id={task_id})"
            )

            # Wait for result if requested
            if wait_for_result:
                result = await self.queue_manager.get_result(
                    task_id, timeout_seconds=timeout_seconds
                )

                if result:
                    execution_time = (time.time() - start_time) * 1000

                    self._execution_count += 1
                    self._total_execution_time += execution_time

                    return {
                        "status": "completed",
                        "event_id": task_id,
                        "target_agent": target_agent,
                        "result": result.to_dict(),
                        "execution_time_ms": execution_time,
                    }
                else:
                    return {
                        "status": "timeout",
                        "event_id": task_id,
                        "error": f"No result after {timeout_seconds}s",
                    }
            else:
                # Fire and forget
                self._execution_count += 1

                return {
                    "status": "sent",
                    "event_id": task_id,
                    "target_agent": target_agent,
                    "message": "Event queued, not waiting for result",
                }

        except Exception as e:
            self.logger.error(f"Event execution error: {e}")
            return {
                "status": "failed",
                "error": str(e),
            }
