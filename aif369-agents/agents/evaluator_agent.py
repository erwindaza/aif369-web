"""Evaluator Agent - Grades student submissions

Responsibilities:
- Score quizzes, labs, case studies
- Provide rubric-based feedback
- Identify learning gaps
- Generate coaching suggestions
"""
import asyncio
import json
from typing import Any, Dict, Optional, List
import ollama
from models import Task
from agents.base import BaseAgent
from config import ConfigManager
from core import QueueManager


class EvaluatorAgent(BaseAgent):
    """
    Evaluator Worker Agent for AIF369 Master

    Grades and provides feedback on:
    - Knowledge checks (quizzes)
    - Laboratory submissions
    - Case studies
    - Capstone artifacts (uses rubrics)

    Scoring:
    - Quiz: Exact match (A=correct, B/C/D=incorrect)
    - Lab: Rubric-based (completeness, quality, testing)
    - Capstone: Multi-criteria (architecture, documentation, compliance)
    """

    def __init__(self):
        super().__init__(agent_id="evaluator", model_name="mistral:7b")
        self.config = ConfigManager.get_instance()
        self.client = ollama.Client(host=self.config.ollama_host)
        self.queue_manager = QueueManager.get_instance()

        # Default rubrics
        self.rubrics = self._load_rubrics()

    def _load_rubrics(self) -> Dict:
        """Load default rubrics"""
        return {
            "quiz": {
                "correct": 100,
                "incorrect": 0,
            },
            "lab": {
                "completeness": 40,  # All steps done
                "correctness": 40,  # Works as expected
                "quality": 20,  # Code/documentation quality
            },
            "case_study": {
                "understanding": 30,
                "analysis": 30,
                "recommendations": 20,
                "clarity": 20,
            },
        }

    async def _process(self, task: Task) -> dict:
        """
        Evaluate student submission

        Payload format:
        {
            "type": "quiz" | "lab" | "case_study",
            "submission": str,
            "expected": str,
            "rubric": dict (optional)
        }
        """
        payload = task.payload
        submission_type = payload.get("type", "quiz")
        submission = payload.get("submission", "")
        expected = payload.get("expected", "")
        rubric = payload.get("rubric") or self.rubrics.get(submission_type)

        try:
            if submission_type == "quiz":
                result = self._grade_quiz(submission, expected)
            elif submission_type == "lab":
                result = await self._grade_lab(submission, rubric)
            elif submission_type == "case_study":
                result = await self._grade_case_study(submission, rubric)
            else:
                result = {"status": "error", "error": f"Unknown type: {submission_type}"}

            return result

        except Exception as e:
            self.logger.error(f"Evaluator error: {e}")
            raise

    def _grade_quiz(self, submission: str, expected: str) -> dict:
        """Grade quiz submission (exact match)"""
        is_correct = submission.strip().upper() == expected.strip().upper()

        score = 100 if is_correct else 0
        feedback = (
            "✓ Correcto" if is_correct else f"✗ Incorrecto. Respuesta correcta: {expected}"
        )

        return {
            "status": "success",
            "score": score,
            "feedback": feedback,
            "type": "quiz",
            "agent": "evaluator",
        }

    async def _grade_lab(self, submission: str, rubric: dict) -> dict:
        """Grade lab submission using rubric"""
        # Criteria:
        # 1. Completeness: All steps documented?
        # 2. Correctness: Code runs? Tests pass?
        # 3. Quality: Well-structured? Documented?

        prompt = self._build_lab_grading_prompt(submission, rubric)

        try:
            response = await asyncio.to_thread(
                self.client.generate,
                model=self.model_name,
                prompt=prompt,
                stream=False,
                options={"temperature": 0.5, "num_predict": 500},
            )

            content = response.get("response", "")
            scores = self._parse_rubric_scores(content, rubric)
            total_score = sum(scores.values())
            feedback = self._generate_lab_feedback(scores, content)

            return {
                "status": "success",
                "score": total_score,
                "max_score": 100,
                "breakdown": scores,
                "feedback": feedback,
                "type": "lab",
                "agent": "evaluator",
                "areas_to_improve": self._identify_gaps(scores),
            }

        except Exception as e:
            self.logger.error(f"Lab grading error: {e}")
            raise

    async def _grade_case_study(self, submission: str, rubric: dict) -> dict:
        """Grade case study using rubric"""
        prompt = self._build_case_study_grading_prompt(submission, rubric)

        try:
            response = await asyncio.to_thread(
                self.client.generate,
                model=self.model_name,
                prompt=prompt,
                stream=False,
                options={"temperature": 0.5, "num_predict": 600},
            )

            content = response.get("response", "")
            scores = self._parse_rubric_scores(content, rubric)
            total_score = sum(scores.values())
            feedback = self._generate_case_study_feedback(scores, content)

            return {
                "status": "success",
                "score": total_score,
                "max_score": 100,
                "breakdown": scores,
                "feedback": feedback,
                "type": "case_study",
                "agent": "evaluator",
                "coaching": self._generate_coaching(scores),
            }

        except Exception as e:
            self.logger.error(f"Case study grading error: {e}")
            raise

    # ─────────────────────────────────────────────────────────────
    # Prompt builders
    # ─────────────────────────────────────────────────────────────

    def _build_lab_grading_prompt(self, submission: str, rubric: dict) -> str:
        """Build prompt for lab grading"""
        criteria = "\n".join(
            [f"- {k}: {v} points" for k, v in rubric.items()]
        )

        return f"""Eres evaluador de laboratorios técnicos.

RUBRIC:
{criteria}

STUDENT SUBMISSION:
{submission[:1000]}

Evaluate the submission on each criterion:
1. Completeness: Are all required steps documented? (0-{rubric.get('completeness', 40)})
2. Correctness: Does the code/solution work? ({rubric.get('correctness', 40)})
3. Quality: Is it well-written, documented, production-ready? ({rubric.get('quality', 20)})

OUTPUT FORMAT:
Completeness: [score] - [reason]
Correctness: [score] - [reason]
Quality: [score] - [reason]
TOTAL: [score]/100
FEEDBACK: [1-2 sentences]

Evaluate:"""

    def _build_case_study_grading_prompt(self, submission: str, rubric: dict) -> str:
        """Build prompt for case study grading"""
        criteria = "\n".join([f"- {k}: {v} points" for k, v in rubric.items()])

        return f"""Eres evaluador de case studies empresariales.

RUBRIC:
{criteria}

STUDENT ANSWER:
{submission[:1200]}

Score on:
1. Understanding: Shows comprehension of the scenario?
2. Analysis: Identifies key issues and root causes?
3. Recommendations: Proposes concrete, justified solutions?
4. Clarity: Well-organized and professional?

OUTPUT:
Understanding: [score] - [reason]
Analysis: [score] - [reason]
Recommendations: [score] - [reason]
Clarity: [score] - [reason]
TOTAL: [score]/100
COACHING: [1-2 suggestions for improvement]

Evaluate:"""

    # ─────────────────────────────────────────────────────────────
    # Parsing & feedback generation
    # ─────────────────────────────────────────────────────────────

    def _parse_rubric_scores(self, content: str, rubric: dict) -> dict:
        """Parse scores from rubric evaluation"""
        scores = {}
        lines = content.split("\n")

        for line in lines:
            for criterion in rubric.keys():
                if criterion in line.lower() and ":" in line:
                    try:
                        # Extract number before '-'
                        score_str = line.split(":")[1].split("-")[0].strip()
                        score = int("".join(filter(str.isdigit, score_str)) or "0")
                        scores[criterion] = min(score, rubric[criterion])
                    except:
                        scores[criterion] = 0

        # Ensure all criteria have scores
        for criterion, max_score in rubric.items():
            if criterion not in scores:
                scores[criterion] = 0

        return scores

    def _generate_lab_feedback(self, scores: dict, content: str) -> str:
        """Generate encouraging lab feedback"""
        avg_score = sum(scores.values()) / len(scores) if scores else 0

        if avg_score >= 90:
            tone = "Excelente trabajo. "
        elif avg_score >= 75:
            tone = "Buen trabajo. "
        elif avg_score >= 60:
            tone = "Tienes la idea, pero hay áreas para mejorar. "
        else:
            tone = "Necesita más trabajo. "

        return f"{tone}Revisa los criterios más bajos y vuelve a intentar."

    def _generate_case_study_feedback(self, scores: dict, content: str) -> str:
        """Generate case study feedback"""
        lowest = min(scores.items(), key=lambda x: x[1])
        return f"Focus on improving {lowest[0].replace('_', ' ')} - that's your weakest area."

    def _identify_gaps(self, scores: dict) -> List[str]:
        """Identify learning gaps from scores"""
        gaps = []
        for criterion, score in scores.items():
            if score < 70:
                gaps.append(f"Necesita mejora en: {criterion}")
        return gaps

    def _generate_coaching(self, scores: dict) -> str:
        """Generate personalized coaching suggestions"""
        if scores.get("understanding", 0) < 70:
            return "Re-read the scenario and identify all stakeholders and constraints."
        elif scores.get("analysis", 0) < 70:
            return "Use the Five Whys technique to dig deeper into root causes."
        elif scores.get("recommendations", 0) < 70:
            return "For each recommendation, explain: What? Why? How? Cost-benefit?"
        else:
            return "Great analysis! Now work on clarity and presentation."

    def __repr__(self) -> str:
        return f"<EvaluatorAgent - {self.model_name}>"
