#!/usr/bin/env python3
"""
SPRINT 1: Batch content generation for AIF369 Master

Generates:
- 24 lessons (Months 1-6, 4 modules each)
- 12 labs (2 per month)
- All with compliance review
- Month 1 approved and ready to publish

Usage:
  python scripts/generate_content_batch.py --months 1-6 --save-to-db
"""
import asyncio
import json
import sys
from typing import List, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from agents import InstructorAgent, ComplianceAgent
from models import Task
from core import LoggerManager, QueueManager

logger = LoggerManager.get_logger("BatchGenerator")
queue_manager = QueueManager.get_instance()


@dataclass
class GenerationStats:
    lessons_generated: int = 0
    lessons_approved: int = 0
    lessons_rejected: int = 0
    labs_generated: int = 0
    labs_approved: int = 0
    labs_rejected: int = 0
    total_time_seconds: float = 0
    start_time: datetime = None

    def elapsed(self):
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0

    def rate(self):
        """Items per minute"""
        total = self.lessons_generated + self.labs_generated
        minutes = self.elapsed() / 60
        if minutes > 0:
            return total / minutes
        return 0

    def summary(self):
        return f"""
╔════════════════════════════════════════════╗
║         SPRINT 1 GENERATION COMPLETE        ║
╠════════════════════════════════════════════╣
║ Lessons Generated:  {self.lessons_generated:3d}               ║
║ Lessons Approved:   {self.lessons_approved:3d}               ║
║ Lessons Rejected:   {self.lessons_rejected:3d}               ║
║                                            ║
║ Labs Generated:     {self.labs_generated:3d}               ║
║ Labs Approved:      {self.labs_approved:3d}               ║
║ Labs Rejected:      {self.labs_rejected:3d}               ║
║                                            ║
║ Total Time:         {self.elapsed():.1f}s              ║
║ Generation Rate:    {self.rate():.2f} items/min          ║
╚════════════════════════════════════════════╝
"""


class BatchContentGenerator:
    def __init__(self):
        self.instructor = InstructorAgent()
        self.compliance = ComplianceAgent()
        self.curriculum = self._load_curriculum()
        self.stats = GenerationStats()
        self.stats.start_time = datetime.now()

    def _load_curriculum(self) -> Dict:
        """Load Master curriculum specification"""
        spec_path = Path("aif369_master_data_ai_governance.json")
        if not spec_path.exists():
            logger.error(f"Curriculum spec not found: {spec_path}")
            sys.exit(1)

        with open(spec_path, "r") as f:
            return json.load(f)

    async def generate_lessons(self, months: List[int]) -> Dict[str, Any]:
        """Generate lessons for specified months"""
        logger.info(f"Starting lesson generation for months: {months}")
        results = {"lessons": {}, "skipped": []}

        curriculum = self.curriculum["curriculum"]["months"]

        for month_spec in curriculum:
            month_num = month_spec["month"]

            if month_num not in months:
                continue

            modules = month_spec.get("modules", [])
            logger.info(f"Month {month_num}: Generating {len(modules)} lessons")

            for module_title in modules:
                try:
                    # Find learning outcomes for this module
                    learning_objectives = self.curriculum["learning_outcomes"][:2]

                    lesson_payload = {
                        "action": "generate_lesson",
                        "month": month_num,
                        "module": module_title,
                        "learning_objectives": learning_objectives,
                        "topic": module_title,
                        "difficulty": "intermediate",
                    }

                    logger.info(
                        f"  Generating: Month {month_num} - {module_title}"
                    )

                    # Generate lesson
                    task = Task(
                        task_id=f"lesson_m{month_num}_mod{modules.index(module_title)}",
                        agent_type="instructor",
                        payload=lesson_payload,
                        priority=1,
                    )

                    result = await self.instructor.execute(task)

                    if result.status != "success":
                        logger.error(f"    ✗ Generation failed")
                        self.stats.lessons_rejected += 1
                        continue

                    lesson_content = result.output.get("lesson", {})
                    self.stats.lessons_generated += 1

                    # Compliance check
                    compliance_task = Task(
                        task_id=f"comp_lesson_m{month_num}",
                        agent_type="compliance",
                        payload={
                            "content": json.dumps(lesson_content),
                            "type": "lesson",
                            "month": month_num,
                        },
                        priority=3,
                    )

                    compliance_result = await self.compliance.execute(
                        compliance_task
                    )

                    review_status = (
                        compliance_result.output.get("review", {}).get("status")
                    )

                    if review_status == "approved":
                        self.stats.lessons_approved += 1
                        status_icon = "✓"
                    else:
                        self.stats.lessons_rejected += 1
                        status_icon = "⚠"

                    logger.info(
                        f"    {status_icon} {module_title} - "
                        f"Compliance: {review_status}"
                    )

                    # Store result
                    lesson_key = f"m{month_num}_{module_title.replace(' ', '_')}"
                    results["lessons"][lesson_key] = {
                        "content": lesson_content,
                        "compliance_status": review_status,
                        "issues": (
                            compliance_result.output.get("review", {}).get("issues", [])
                        ),
                    }

                except Exception as e:
                    logger.error(f"    ✗ Exception: {e}")
                    self.stats.lessons_rejected += 1
                    results["skipped"].append(
                        {"month": month_num, "module": module_title, "error": str(e)}
                    )

        return results

    async def generate_labs(self, months: List[int]) -> Dict[str, Any]:
        """Generate labs for specified months"""
        logger.info(f"Starting lab generation for months: {months}")
        results = {"labs": {}, "skipped": []}

        curriculum = self.curriculum["curriculum"]["months"]
        topics = [
            "Cloud Architecture",
            "Data Governance",
            "Security Implementation",
            "Privacy Compliance",
            "AI Governance",
            "Architecture Design",
        ]

        for month_spec in curriculum:
            month_num = month_spec["month"]

            if month_num not in months:
                continue

            # Generate 2 labs per month
            for lab_num in range(1, 3):
                try:
                    topic = topics[(month_num + lab_num) % len(topics)]
                    difficulty = "intermediate" if lab_num == 1 else "advanced"

                    lab_payload = {
                        "action": "generate_lab",
                        "month": month_num,
                        "topic": topic,
                        "difficulty": difficulty,
                    }

                    logger.info(
                        f"  Generating: Month {month_num} - Lab {lab_num} ({topic})"
                    )

                    task = Task(
                        task_id=f"lab_m{month_num}_l{lab_num}",
                        agent_type="instructor",
                        payload=lab_payload,
                        priority=1,
                    )

                    result = await self.instructor.execute(task)

                    if result.status != "success":
                        logger.error(f"    ✗ Generation failed")
                        self.stats.labs_rejected += 1
                        continue

                    lab_content = result.output.get("lab", {})
                    self.stats.labs_generated += 1

                    # Compliance check
                    compliance_task = Task(
                        task_id=f"comp_lab_m{month_num}_l{lab_num}",
                        agent_type="compliance",
                        payload={
                            "content": json.dumps(lab_content),
                            "type": "lab",
                            "month": month_num,
                        },
                        priority=3,
                    )

                    compliance_result = await self.compliance.execute(
                        compliance_task
                    )

                    review_status = (
                        compliance_result.output.get("review", {}).get("status")
                    )

                    if review_status == "approved":
                        self.stats.labs_approved += 1
                        status_icon = "✓"
                    else:
                        self.stats.labs_rejected += 1
                        status_icon = "⚠"

                    logger.info(
                        f"    {status_icon} Lab {lab_num}: {topic} - "
                        f"Compliance: {review_status}"
                    )

                    # Store result
                    lab_key = f"m{month_num}_lab{lab_num}_{topic.replace(' ', '_')}"
                    results["labs"][lab_key] = {
                        "content": lab_content,
                        "compliance_status": review_status,
                        "issues": (
                            compliance_result.output.get("review", {}).get("issues", [])
                        ),
                    }

                except Exception as e:
                    logger.error(f"    ✗ Exception: {e}")
                    self.stats.labs_rejected += 1
                    results["skipped"].append(
                        {"month": month_num, "lab": lab_num, "error": str(e)}
                    )

        return results

    async def run(self, months: List[int]):
        """Run full generation pipeline"""
        logger.info(
            f"╔════════════════════════════════════════════╗"
        )
        logger.info(
            f"║      SPRINT 1: BATCH CONTENT GENERATION      ║"
        )
        logger.info(
            f"║  Months: {str(months):30s}  ║"
        )
        logger.info(
            f"╚════════════════════════════════════════════╝"
        )

        try:
            # Generate lessons
            lesson_results = await self.generate_lessons(months)

            # Generate labs
            lab_results = await self.generate_labs(months)

            # Save results
            output = {
                "timestamp": datetime.now().isoformat(),
                "months": months,
                "lessons": lesson_results,
                "labs": lab_results,
                "stats": {
                    "lessons_generated": self.stats.lessons_generated,
                    "lessons_approved": self.stats.lessons_approved,
                    "lessons_rejected": self.stats.lessons_rejected,
                    "labs_generated": self.stats.labs_generated,
                    "labs_approved": self.stats.labs_approved,
                    "labs_rejected": self.stats.labs_rejected,
                    "total_time_seconds": self.stats.elapsed(),
                },
            }

            # Save to file
            output_path = Path("output") / f"sprint1_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            output_path.parent.mkdir(exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(output, f, indent=2)

            logger.info(f"\n✓ Results saved to: {output_path}")

            # Print summary
            print(self.stats.summary())

            return output

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            raise


async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate AIF369 Master content in batch"
    )
    parser.add_argument(
        "--months",
        type=str,
        default="1-3",
        help="Months to generate (e.g. 1-6 or 1,3,5)",
    )
    parser.add_argument(
        "--save-to-db",
        action="store_true",
        help="Save generated content to database",
    )

    args = parser.parse_args()

    # Parse month range
    if "-" in args.months:
        start, end = map(int, args.months.split("-"))
        months = list(range(start, end + 1))
    else:
        months = list(map(int, args.months.split(",")))

    logger.info(f"Generating content for months: {months}")

    generator = BatchContentGenerator()
    results = await generator.run(months)

    if args.save_to_db:
        logger.info("Saving to database... (TODO: implement DB save)")

    logger.info("✓ SPRINT 1 batch generation complete!")

    return results


if __name__ == "__main__":
    asyncio.run(main())
