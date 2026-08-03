"""Test Master program agents

Test Instructor, Evaluator, Compliance agents
"""
import sys
import os
from pathlib import Path

# Ensure parent directory is in path BEFORE any other imports
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Change to parent directory for imports to work
os.chdir(Path(__file__).parent.parent)

import asyncio
import pytest
from models.task import Task
from agents.instructor_agent import InstructorAgent
from agents.evaluator_agent import EvaluatorAgent
from agents.compliance_agent import ComplianceAgent


@pytest.mark.asyncio
async def test_instructor_agent_generates_lesson():
    """Test Instructor Agent can generate a lesson"""
    agent = InstructorAgent()

    task = Task(
        task_id="test_lesson_001",
        agent_type="instructor",
        payload={
            "action": "generate_lesson",
            "month": 1,
            "module": "Enterprise Architecture Fundamentals",
            "learning_objectives": [
                "Understand TOGAF ADM",
                "Apply principles of architecture",
            ],
            "topic": "Architecture Framework Overview",
        },
        priority=1,
    )

    result = await agent.execute(task)

    assert result.status == "success"
    assert result.output["status"] == "success"
    assert "lesson" in result.output
    assert result.output["lesson"]["month"] == 1
    assert len(result.output["lesson"]["content_sections"]) > 0
    print(f"✓ Instructor generated lesson with {len(result.output['lesson']['content_sections'])} sections")


@pytest.mark.asyncio
async def test_instructor_agent_generates_lab():
    """Test Instructor Agent can generate a lab"""
    agent = InstructorAgent()

    task = Task(
        task_id="test_lab_001",
        agent_type="instructor",
        payload={
            "action": "generate_lab",
            "month": 3,
            "topic": "Data Governance",
            "difficulty": "intermediate",
        },
        priority=1,
    )

    result = await agent.execute(task)

    assert result.status == "success"
    assert "lab" in result.output
    assert result.output["lab"]["month"] == 3
    assert len(result.output["lab"]["steps"]) > 0
    print(f"✓ Instructor generated lab with {len(result.output['lab']['steps'])} steps")


@pytest.mark.asyncio
async def test_evaluator_agent_grades_quiz():
    """Test Evaluator Agent grades quiz correctly"""
    agent = EvaluatorAgent()

    task = Task(
        task_id="test_quiz_001",
        agent_type="evaluator",
        payload={
            "type": "quiz",
            "submission": "A",
            "expected": "A",
        },
        priority=1,
    )

    result = await agent.execute(task)

    assert result.status == "success"
    assert result.output["score"] == 100
    print("✓ Evaluator correctly graded quiz (A=correct)")

    # Test incorrect answer
    task2 = Task(
        task_id="test_quiz_002",
        agent_type="evaluator",
        payload={
            "type": "quiz",
            "submission": "B",
            "expected": "A",
        },
        priority=1,
    )

    result2 = await agent.execute(task2)
    assert result2.output["score"] == 0
    print("✓ Evaluator correctly graded quiz (B=incorrect)")


@pytest.mark.asyncio
async def test_compliance_agent_detects_copyright():
    """Test Compliance Agent detects copyright issues"""
    agent = ComplianceAgent()

    # Content with obvious copyright pattern
    task = Task(
        task_id="test_compliance_001",
        agent_type="compliance",
        payload={
            "content": "ISO/IEC 27001:2022 establece los requisitos para un sistema de gestión de seguridad de la información.",
            "type": "lesson",
        },
        priority=1,
    )

    result = await agent.execute(task)

    assert result.status == "success"
    review = result.output["review"]
    assert review["status"] in ["rejected", "needs_review"]
    print(f"✓ Compliance detected copyright issue: {review['status']}")


@pytest.mark.asyncio
async def test_compliance_agent_approves_good_content():
    """Test Compliance Agent approves compliant content"""
    agent = ComplianceAgent()

    # Good content (paraphrased, cited)
    task = Task(
        task_id="test_compliance_002",
        agent_type="compliance",
        payload={
            "content": "Los sistemas de información requieren controles de seguridad. Según ISO/IEC 27001:2022, estos incluyen identificación y autenticación. Fuente: https://iso.org",
            "type": "lesson",
        },
        priority=1,
    )

    result = await agent.execute(task)

    assert result.status == "success"
    review = result.output["review"]
    assert review["status"] in ["approved", "needs_review"]
    print(f"✓ Compliance approved good content: {review['status']}")


@pytest.mark.asyncio
async def test_compliance_agent_rejects_false_claims():
    """Test Compliance Agent rejects false accreditation"""
    agent = ComplianceAgent()

    task = Task(
        task_id="test_compliance_003",
        agent_type="compliance",
        payload={
            "content": "This course is officially accredited by TOGAF and ISO/IEC 27001.",
            "type": "lesson",
        },
        priority=1,
    )

    result = await agent.execute(task)

    assert result.status == "success"
    review = result.output["review"]
    assert review["status"] == "rejected"
    print(f"✓ Compliance rejected false accreditation claim")


if __name__ == "__main__":
    # Run tests
    print("\n=== Testing Master Program Agents ===\n")

    # Test 1: Instructor generates lesson
    asyncio.run(test_instructor_agent_generates_lesson())

    # Test 2: Instructor generates lab
    asyncio.run(test_instructor_agent_generates_lab())

    # Test 3: Evaluator grades quiz
    asyncio.run(test_evaluator_agent_grades_quiz())

    # Test 4: Compliance detects copyright
    asyncio.run(test_compliance_agent_detects_copyright())

    # Test 5: Compliance approves good content
    asyncio.run(test_compliance_agent_approves_good_content())

    # Test 6: Compliance rejects false claims
    asyncio.run(test_compliance_agent_rejects_false_claims())

    print("\n=== All tests passed! ===\n")
