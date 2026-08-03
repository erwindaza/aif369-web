"""FastAPI routes for AIF369 Master program

Endpoints for:
- Lesson generation (Instructor Agent)
- Content evaluation (Evaluator Agent)
- Compliance review (Compliance Agent)
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from models import Task, AgentType, TaskStatus
from agents import InstructorAgent, EvaluatorAgent, ComplianceAgent
from core import QueueManager, LoggerManager
import asyncio

router = APIRouter(prefix="/api/master", tags=["master"])
logger = LoggerManager.get_logger("MasterRoutes")
queue_manager = QueueManager.get_instance()


# ─────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────


class GenerateLessonRequest(BaseModel):
    month: int
    module: str
    learning_objectives: List[str]
    topic: str
    difficulty: Optional[str] = "intermediate"


class GenerateLabRequest(BaseModel):
    month: int
    topic: str
    difficulty: Optional[str] = "intermediate"


class EvaluateRequest(BaseModel):
    type: str  # quiz | lab | case_study
    submission: str
    expected: Optional[str] = None  # For quiz
    rubric: Optional[Dict[str, int]] = None  # For lab/case_study


class ComplianceRequest(BaseModel):
    content: str
    type: str  # lesson | lab | capstone
    month: Optional[int] = None


# ─────────────────────────────────────────────────────────────
# Lesson Generation
# ─────────────────────────────────────────────────────────────


@router.post("/lessons")
async def generate_lesson(req: GenerateLessonRequest, background_tasks: BackgroundTasks):
    """Generate a lesson using Instructor Agent"""
    try:
        task = Task(
            task_id=f"lesson_{req.month}_{req.module.replace(' ', '_')}",
            agent_type="instructor",
            payload={
                "action": "generate_lesson",
                "month": req.month,
                "module": req.module,
                "learning_objectives": req.learning_objectives,
                "topic": req.topic,
                "difficulty": req.difficulty,
            },
            priority=1,
        )

        # Submit to queue (non-blocking)
        task_id = await queue_manager.enqueue_task(task)
        logger.info(f"Lesson generation queued: {task_id}")

        return {
            "task_id": task_id,
            "status": "queued",
            "message": f"Generating lesson for {req.module}",
        }

    except Exception as e:
        logger.error(f"Error queuing lesson: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lessons/{lesson_id}")
async def get_lesson_result(lesson_id: str):
    """Get generated lesson result"""
    try:
        result = await queue_manager.get_result(lesson_id, timeout_seconds=30)

        if result is None:
            return {"status": "pending", "lesson_id": lesson_id}

        return {"status": "completed", "result": result}

    except Exception as e:
        logger.error(f"Error retrieving lesson: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Lab Generation
# ─────────────────────────────────────────────────────────────


@router.post("/labs")
async def generate_lab(req: GenerateLabRequest):
    """Generate a lab using Instructor Agent"""
    try:
        task = Task(
            task_id=f"lab_{req.month}_{req.topic.replace(' ', '_')}",
            agent_type="instructor",
            payload={
                "action": "generate_lab",
                "month": req.month,
                "topic": req.topic,
                "difficulty": req.difficulty,
            },
            priority=1,
        )

        task_id = await queue_manager.enqueue_task(task)
        logger.info(f"Lab generation queued: {task_id}")

        return {
            "task_id": task_id,
            "status": "queued",
            "message": f"Generating lab for {req.topic}",
        }

    except Exception as e:
        logger.error(f"Error queuing lab: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Assessment
# ─────────────────────────────────────────────────────────────


@router.post("/assess")
async def evaluate_submission(req: EvaluateRequest):
    """Evaluate student submission using Evaluator Agent"""
    try:
        task = Task(
            task_id=f"eval_{req.type}_{id(req)}",
            agent_type="evaluator",
            payload={
                "type": req.type,
                "submission": req.submission,
                "expected": req.expected,
                "rubric": req.rubric,
            },
            priority=2,  # Higher priority than generation
        )

        task_id = await queue_manager.enqueue_task(task)
        logger.info(f"Evaluation queued: {task_id}")

        return {
            "task_id": task_id,
            "status": "queued",
            "message": f"Evaluating {req.type} submission",
        }

    except Exception as e:
        logger.error(f"Error queuing evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assess/{task_id}")
async def get_evaluation_result(task_id: str):
    """Get evaluation result"""
    try:
        result = await queue_manager.get_result(task_id, timeout_seconds=10)

        if result is None:
            return {"status": "pending", "task_id": task_id}

        return {"status": "completed", "result": result}

    except Exception as e:
        logger.error(f"Error retrieving evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Compliance Review
# ─────────────────────────────────────────────────────────────


@router.post("/compliance/review")
async def review_content(req: ComplianceRequest):
    """Review content for compliance using Compliance Agent"""
    try:
        task = Task(
            task_id=f"compliance_{req.type}_{id(req)}",
            agent_type="compliance",
            payload={
                "content": req.content,
                "type": req.type,
                "month": req.month,
            },
            priority=3,  # Highest priority for blocking
        )

        task_id = await queue_manager.enqueue_task(task)
        logger.info(f"Compliance review queued: {task_id}")

        return {
            "task_id": task_id,
            "status": "queued",
            "message": f"Reviewing {req.type} for compliance",
        }

    except Exception as e:
        logger.error(f"Error queuing compliance review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/review/{task_id}")
async def get_compliance_result(task_id: str):
    """Get compliance review result"""
    try:
        result = await queue_manager.get_result(task_id, timeout_seconds=5)

        if result is None:
            return {"status": "pending", "task_id": task_id}

        return {"status": "completed", "result": result}

    except Exception as e:
        logger.error(f"Error retrieving compliance result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Blocking variants (for synchronous callers)
# ─────────────────────────────────────────────────────────────


@router.post("/lessons/and-wait")
async def generate_lesson_and_wait(req: GenerateLessonRequest):
    """Generate lesson and wait for result (blocking)"""
    try:
        task = Task(
            task_id=f"lesson_{req.month}_{req.module.replace(' ', '_')}",
            agent_type="instructor",
            payload={
                "action": "generate_lesson",
                "month": req.month,
                "module": req.module,
                "learning_objectives": req.learning_objectives,
                "topic": req.topic,
            },
            priority=1,
        )

        # Use orchestrator directly for blocking call
        from orchestrator.orchestrator import Orchestrator

        orchestrator = Orchestrator()
        result = await orchestrator.submit_and_wait(task, timeout_seconds=60)

        return {"status": result.status, "output": result.output}

    except Exception as e:
        logger.error(f"Error generating lesson: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assess/and-wait")
async def evaluate_and_wait(req: EvaluateRequest):
    """Evaluate and wait for result (blocking)"""
    try:
        task = Task(
            task_id=f"eval_{req.type}_{id(req)}",
            agent_type="evaluator",
            payload={
                "type": req.type,
                "submission": req.submission,
                "expected": req.expected,
                "rubric": req.rubric,
            },
            priority=2,
        )

        from orchestrator.orchestrator import Orchestrator

        orchestrator = Orchestrator()
        result = await orchestrator.submit_and_wait(task, timeout_seconds=15)

        return {"status": result.status, "output": result.output}

    except Exception as e:
        logger.error(f"Error evaluating: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance/review/and-wait")
async def review_and_wait(req: ComplianceRequest):
    """Review for compliance and wait (blocking)"""
    try:
        task = Task(
            task_id=f"compliance_{req.type}_{id(req)}",
            agent_type="compliance",
            payload={
                "content": req.content,
                "type": req.type,
                "month": req.month,
            },
            priority=3,
        )

        from orchestrator.orchestrator import Orchestrator

        orchestrator = Orchestrator()
        result = await orchestrator.submit_and_wait(task, timeout_seconds=10)

        return {"status": result.status, "output": result.output}

    except Exception as e:
        logger.error(f"Error in compliance review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────


@router.get("/health")
async def health_check():
    """Health check for Master API"""
    return {
        "status": "ok",
        "service": "aif369-master",
        "agents": ["instructor", "evaluator", "compliance"],
    }
