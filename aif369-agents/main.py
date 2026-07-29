"""FastAPI main application - Agent orchestration server"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from models import Task, AgentType, TaskStatus
from orchestrator.orchestrator import Orchestrator
from core import LoggerManager, QueueManager


# ─── Pydantic Models (API schemas only) ───────────────────────────────────

class TaskRequest(BaseModel):
    """API request to submit a task"""
    agent_type: str  # "v1_mistral" or "v2_llama"
    payload: dict
    priority: int = 1
    timeout_seconds: int = 30

    class Config:
        json_schema_extra = {
            "example": {
                "agent_type": "v1_mistral",
                "payload": {
                    "title": "Laptop Pro 15",
                    "description": "High-performance laptop",
                    "price": 999.99,
                },
                "priority": 1,
                "timeout_seconds": 30,
            }
        }


class WhatsAppMessage(BaseModel):
    """WhatsApp webhook message"""
    from_: str  # Customer phone number
    body: str  # Message text
    message_id: Optional[str] = None
    timestamp: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "from_": "+56912345678",
                "body": "Hola, tengo una pregunta sobre...",
                "message_id": "msg_123",
                "timestamp": "2026-07-29T10:00:00Z",
            }
        }


class ResultResponse(BaseModel):
    """API response with result"""
    task_id: str
    status: str
    output: Optional[dict]
    execution_time_ms: float
    error: Optional[str] = None
    agent_used: Optional[str] = None


# ─── Lifecycle Management ───────────────────────────────────────────────────

logger = LoggerManager.get_logger("Main")
orchestrator = Orchestrator()
task_processor_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager
    - Startup: initialize orchestrator, start task processor
    - Shutdown: gracefully stop all components
    """
    # Startup
    logger.info("🚀 Starting aif369-agents orchestrator")

    await orchestrator.initialize()

    # Start background task processor
    global task_processor_task
    task_processor_task = asyncio.create_task(orchestrator.process_tasks())

    logger.info("✅ Orchestrator ready")

    yield  # App runs here

    # Shutdown
    logger.info("🛑 Shutting down orchestrator")

    if task_processor_task:
        task_processor_task.cancel()
        try:
            await task_processor_task
        except asyncio.CancelledError:
            pass

    await orchestrator.shutdown()
    logger.info("✅ Shutdown complete")


# ─── FastAPI App ───────────────────────────────────────────────────────────

app = FastAPI(
    title="aif369 Agents Orchestrator",
    description="Multi-agent system: Mistral 7B (V1) + Llama 70B (V2)",
    version="0.1.0",
    lifespan=lifespan,
)


# ─── Health Check ──────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check():
    """Liveness check"""
    return {
        "status": "healthy",
        "orchestrator": str(orchestrator),
        "task_processor": "running" if task_processor_task and not task_processor_task.done() else "stopped",
    }


@app.get("/stats", tags=["System"])
async def get_stats():
    """Get system statistics"""
    stats = await orchestrator.get_system_stats()
    return stats


# ─── Task API ──────────────────────────────────────────────────────────────

@app.post("/submit", tags=["Tasks"], response_model=dict)
async def submit_task(request: TaskRequest):
    """
    Submit a task to the orchestrator

    - **agent_type**: "v1_mistral" (fast, Mistral 7B) or "v2_llama" (accurate, Llama 70B)
    - **payload**: task data (product info, etc)
    - **priority**: 1-10 (higher = faster)
    - **timeout_seconds**: max execution time

    Returns: task_id for polling

    Latency: <10ms (queued, non-blocking)
    """
    try:
        agent_type = AgentType(request.agent_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent_type. Use 'v1_mistral' or 'v2_llama'",
        )

    task = Task(
        task_id=f"{request.agent_type}_{int(__import__('time').time() * 1000)}",
        agent_type=agent_type,
        payload=request.payload,
        priority=request.priority,
        timeout_seconds=request.timeout_seconds,
    )

    task_id = await orchestrator.submit_task(task)

    return {
        "task_id": task_id,
        "status": "queued",
        "message": "Task queued for processing",
    }


@app.get("/result/{task_id}", tags=["Tasks"], response_model=dict)
async def get_result(task_id: str, wait_ms: int = 0):
    """
    Get result for a task

    - **task_id**: task identifier from /submit
    - **wait_ms**: poll interval (0 = return immediately)

    Returns: result or 404 if not found

    Polling: call repeatedly until status != 'processing'
    """
    queue_manager = QueueManager.get_instance()

    result = None
    if wait_ms > 0:
        # Poll with timeout
        import time
        start = time.time()
        while (time.time() - start) * 1000 < wait_ms:
            result = await queue_manager.get_result(
                task_id, timeout_seconds=wait_ms / 1000
            )
            if result:
                break
            await asyncio.sleep(0.05)
    else:
        # Check immediately (may not be ready)
        result = await queue_manager.get_result(task_id, timeout_seconds=0)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Result not found for task {task_id}. Still processing?",
        )

    return result.to_dict()


@app.post("/submit_and_wait", tags=["Tasks"], response_model=dict)
async def submit_and_wait(request: TaskRequest):
    """
    Submit task and wait for result (blocking)

    Use this for synchronous requests. Returns immediately when task completes.

    Warning: This is blocking. For high-throughput, use /submit + polling.

    Latency: depends on task complexity
    - V1 (Mistral 7B): typically 0.4-0.6s
    - V2 (Llama 70B): typically 0.8-1.2s
    """
    try:
        agent_type = AgentType(request.agent_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent_type. Use 'v1_mistral' or 'v2_llama'",
        )

    task = Task(
        task_id=f"{request.agent_type}_{int(__import__('time').time() * 1000)}",
        agent_type=agent_type,
        payload=request.payload,
        priority=request.priority,
        timeout_seconds=request.timeout_seconds,
    )

    result = await orchestrator.submit_and_wait(task)

    return result.to_dict()


# ─── Recurring Tasks (Scheduler) ────────────────────────────────────────────

@app.post("/schedule", tags=["Scheduler"])
async def schedule_recurring_task(
    task_name: str,
    cron_expression: str,
    agent_type: str,
    payload: dict,
):
    """
    Schedule a recurring task

    - **task_name**: unique name for task
    - **cron_expression**: cron format (e.g., "0 * * * *" = every hour)
    - **agent_type**: "v1_mistral" or "v2_llama"
    - **payload**: task data

    Cron Examples:
    - "0 * * * *"     → every hour
    - "0 */6 * * *"   → every 6 hours
    - "0 0 * * 0"     → weekly (Sunday)
    - "0 0 1 * *"     → monthly (1st day)
    """
    try:
        agent_type_enum = AgentType(agent_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent_type. Use 'v1_mistral' or 'v2_llama'",
        )

    try:
        task_id = await orchestrator.run_recurring_task(
            task_name, cron_expression, agent_type_enum, payload
        )
        return {
            "task_name": task_name,
            "task_id": task_id,
            "cron": cron_expression,
            "status": "scheduled",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Error Handler ─────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ─── Root ──────────────────────────────────────────────────────────────────

@app.post("/whatsapp/message", tags=["WhatsApp"])
async def whatsapp_webhook(message: WhatsAppMessage):
    """
    WhatsApp webhook - receive messages from customers

    This endpoint receives messages from the WhatsApp Bot (Node.js)
    and submits them to agents for processing.

    The agent processes the message and responds via WhatsApp
    using the WhatsAppTool.

    Args:
        message: WhatsApp message with from, body, etc

    Returns:
        task_id for tracking
    """
    logger.info(f"WhatsApp message from {message.from_}: {message.body[:50]}...")

    task = Task(
        task_id=message.message_id or f"wsp_{message.from_}_{int(__import__('time').time() * 1000)}",
        agent_type=AgentType.V1_MISTRAL,  # Fast response for customer messages
        payload={
            "message": message.body,
            "customer_phone": message.from_,
            "type": "customer_inquiry",
            "timestamp": message.timestamp,
        },
        priority=2,  # Higher priority for customer messages
        timeout_seconds=20,
    )

    task_id = await orchestrator.submit_task(task)

    return {
        "task_id": task_id,
        "status": "submitted",
        "message": "WhatsApp message queued for processing",
        "customer": message.from_,
    }


@app.get("/", tags=["Info"])
async def root():
    """API information"""
    return {
        "name": "aif369 Agents Orchestrator",
        "version": "0.1.0",
        "agents": [
            {
                "id": "v1_mistral",
                "model": "mistral:7b",
                "generation": "v1_react",
                "latency_ms": "400-600",
                "quality": "good",
            },
            {
                "id": "v2_llama",
                "model": "llama2:70b",
                "generation": "v2_langgraph",
                "latency_ms": "800-1200",
                "quality": "excellent",
            },
        ],
        "endpoints": {
            "health": "GET /health",
            "submit": "POST /submit",
            "result": "GET /result/{task_id}",
            "submit_and_wait": "POST /submit_and_wait",
            "schedule": "POST /schedule",
            "whatsapp": "POST /whatsapp/message",
            "stats": "GET /stats",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
