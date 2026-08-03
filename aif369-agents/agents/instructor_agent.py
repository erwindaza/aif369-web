"""Instructor Agent - Generates lessons for AIF369 Master program

Responsibilities:
- Generate lesson content (learning objectives, sections, examples)
- Create knowledge checks (quiz questions)
- Generate laboratories with step-by-step instructions
- Paraphrase and cite standards (TOGAF, ISO, DAMA)
- Ensure compliance with AIF369 guidelines
"""
import asyncio
import json
from typing import Any, Dict, Optional, List
import ollama
from models import Task
from models.master_models import Lesson, Lab, KnowledgeCheck, ContentSection, Activity
from agents.base import BaseAgent
from config import ConfigManager
from tools import InterAgentEventTool
from core import QueueManager


class InstructorAgent(BaseAgent):
    """
    Instructor Worker Agent for AIF369 Master

    Generates academic content (lessons, labs, quizzes) aligned with:
    - Learning outcomes (Bloom's taxonomy)
    - Competency domains (8 domains)
    - Paraphrasing standards (TOGAF, ISO, DAMA)
    - Citation requirements (official sources)

    Models:
    - Mistral 7B: Fast generation (0.4-0.6s)
    - Claude (API): Higher quality paraphrasing (0.8-1.2s)
    """

    def __init__(self):
        super().__init__(agent_id="instructor", model_name="mistral:7b")
        self.config = ConfigManager.get_instance()
        self.client = ollama.Client(host=self.config.ollama_host)
        self.queue_manager = QueueManager.get_instance()

        # Master curriculum reference
        self.master_curriculum = self._load_master_curriculum()

    def _load_master_curriculum(self) -> Dict:
        """Load AIF369 Master curriculum specification"""
        try:
            with open("aif369_master_data_ai_governance.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning("Master curriculum not found")
            return {}

    async def _process(self, task: Task) -> dict:
        """
        Generate lesson content

        Payload format:
        {
            "action": "generate_lesson" | "generate_lab" | "generate_quiz",
            "month": int (1-12),
            "module": str,
            "learning_objectives": [str],
            "topic": str,
            "difficulty": str (beginner|intermediate|advanced)
        }
        """
        payload = task.payload
        action = payload.get("action", "generate_lesson")

        try:
            if action == "generate_lesson":
                result = await self._generate_lesson(payload)
            elif action == "generate_lab":
                result = await self._generate_lab(payload)
            elif action == "generate_quiz":
                result = await self._generate_quiz(payload)
            else:
                result = {
                    "status": "error",
                    "error": f"Unknown action: {action}",
                }

            return result

        except Exception as e:
            self.logger.error(f"Instructor agent error: {e}")
            raise

    async def _generate_lesson(self, payload: dict) -> dict:
        """Generate a single lesson"""
        month = payload.get("month")
        module = payload.get("module")
        learning_objectives = payload.get("learning_objectives", [])
        topic = payload.get("topic", "")

        # Build prompt with curriculum context
        prompt = self._build_lesson_prompt(month, module, learning_objectives, topic)

        try:
            response = await asyncio.to_thread(
                self.client.generate,
                model=self.model_name,
                prompt=prompt,
                stream=False,
                options={"temperature": 0.7, "num_predict": 1500},
            )

            content = response.get("response", "")

            # Parse sections from response
            sections = self._parse_lesson_sections(content)
            examples = self._extract_examples(content)
            references = self._extract_references(content)

            result = {
                "status": "success",
                "lesson": {
                    "month": month,
                    "module": module,
                    "title": f"{module} - Mes {month}",
                    "summary": self._extract_summary(content),
                    "learning_objectives": learning_objectives,
                    "estimated_minutes": 45 + (month % 5) * 10,  # 45-90 min
                    "content_sections": sections,
                    "examples": examples,
                    "references": references,
                    "requires_legal_review": self._requires_legal_review(content),
                },
                "model_used": self.model_name,
                "agent": "instructor",
            }

            return result

        except Exception as e:
            self.logger.error(f"Lesson generation error: {e}")
            raise

    async def _generate_lab(self, payload: dict) -> dict:
        """Generate a laboratory exercise"""
        month = payload.get("month")
        topic = payload.get("topic", "")
        difficulty = payload.get("difficulty", "intermediate")

        prompt = self._build_lab_prompt(month, topic, difficulty)

        try:
            response = await asyncio.to_thread(
                self.client.generate,
                model=self.model_name,
                prompt=prompt,
                stream=False,
                options={"temperature": 0.6, "num_predict": 1200},
            )

            content = response.get("response", "")

            # Parse lab structure
            steps = self._parse_lab_steps(content)
            setup = self._extract_setup(content)
            validation = self._extract_validation_criteria(content)

            result = {
                "status": "success",
                "lab": {
                    "month": month,
                    "title": f"Lab: {topic} (Mes {month})",
                    "description": self._extract_summary(content),
                    "learning_objectives": [
                        f"Implementar {topic}",
                        "Validar con criterios de aceptación",
                    ],
                    "estimated_hours": 2.0 + (difficulty == "advanced"),
                    "difficulty": difficulty,
                    "setup_instructions": setup,
                    "steps": steps,
                    "validation_criteria": validation,
                    "tools_required": self._infer_tools(topic),
                    "requires_legal_review": False,
                },
                "model_used": self.model_name,
                "agent": "instructor",
            }

            return result

        except Exception as e:
            self.logger.error(f"Lab generation error: {e}")
            raise

    async def _generate_quiz(self, payload: dict) -> dict:
        """Generate knowledge check questions"""
        lesson_topic = payload.get("topic", "")
        difficulty = payload.get("difficulty", "intermediate")
        num_questions = payload.get("num_questions", 5)

        prompt = self._build_quiz_prompt(lesson_topic, difficulty, num_questions)

        try:
            response = await asyncio.to_thread(
                self.client.generate,
                model=self.model_name,
                prompt=prompt,
                stream=False,
                options={"temperature": 0.5, "num_predict": 800},
            )

            content = response.get("response", "")
            questions = self._parse_quiz_questions(content, num_questions)

            result = {
                "status": "success",
                "questions": questions,
                "num_questions": len(questions),
                "model_used": self.model_name,
                "agent": "instructor",
            }

            return result

        except Exception as e:
            self.logger.error(f"Quiz generation error: {e}")
            raise

    # ─────────────────────────────────────────────────────────────
    # Prompt builders
    # ─────────────────────────────────────────────────────────────

    def _build_lesson_prompt(
        self, month: int, module: str, objectives: List[str], topic: str
    ) -> str:
        """Build prompt for lesson generation"""
        objectives_text = "\n".join([f"- {obj}" for obj in objectives])

        return f"""Eres el Instructor del AIF369 Master en Arquitectura, Gobernanza de Datos e IA.

Genera una lección profesional para:
- Mes {month}
- Módulo: {module}
- Tema: {topic}

Learning Objectives:
{objectives_text}

IMPORTANT GUIDELINES:
1. PARAPHRASE, don't copy: If referencing TOGAF, ISO, DAMA, paraphrase + cite
   Example: "Según TOGAF 9.2, la Architecture Development Method (ADM) consiste en..."
2. Include EXAMPLES from Chile/LATAM when possible
3. Structure:
   - Introduction (1 paragraph)
   - Core concepts (3-4 sections)
   - Real-world example (Chile or LATAM)
   - Key takeaway
4. Cite sources: Always indicate "Fuente: [standard/framework]"
5. Avoid copying protected text from standards

EXPECTED OUTPUT FORMAT:
[INTRODUCTION]
[CONCEPT_1_TITLE]
[CONCEPT_1_TEXT]
[CONCEPT_2_TITLE]
[CONCEPT_2_TEXT]
[EXAMPLE]
[REFERENCES: List sources here]

Generate the lesson (max 500 words):"""

    def _build_lab_prompt(self, month: int, topic: str, difficulty: str) -> str:
        """Build prompt for lab generation"""
        return f"""Eres instructor de laboratorios prácticos.

Crea un laboratorio para:
- Mes {month}
- Tema: {topic}
- Dificultad: {difficulty}

Structure:
1. Objective (1 line)
2. Prerequisites
3. Setup (tools, accounts, repos needed)
4. Step-by-step (6-10 steps)
5. Validation criteria (how to verify completion)
6. Expected time: {2 + (difficulty == 'advanced')} hours

Make it:
- Hands-on (not theory)
- Self-contained (runnable in isolation)
- Testable (clear validation criteria)
- Safe (no dangerous operations)

OUTPUT FORMAT:
[OBJECTIVE]
[PREREQUISITES]
[SETUP]
[STEP_1]
[STEP_2]
...
[VALIDATION]

Generate:"""

    def _build_quiz_prompt(self, topic: str, difficulty: str, num_q: int) -> str:
        """Build prompt for quiz generation"""
        return f"""Crea {num_q} preguntas de opción múltiple sobre: {topic}
Dificultad: {difficulty}

Format per question:
Question: [text]
A) [correct answer]
B) [incorrect]
C) [incorrect]
D) [incorrect]
Correct: A

Create {num_q} questions:"""

    # ─────────────────────────────────────────────────────────────
    # Parsing helpers
    # ─────────────────────────────────────────────────────────────

    def _parse_lesson_sections(self, content: str) -> List[dict]:
        """Parse lesson content into sections"""
        sections = []
        lines = content.split("\n")

        current_section = None
        for line in lines:
            if line.startswith("[") and line.endswith("]"):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    "title": line.strip("[]"),
                    "content": "",
                }
            elif current_section:
                current_section["content"] += line + "\n"

        if current_section:
            sections.append(current_section)

        return [
            {"title": s["title"], "content": s["content"].strip()} for s in sections
        ]

    def _parse_lab_steps(self, content: str) -> List[str]:
        """Extract lab steps"""
        steps = []
        for line in content.split("\n"):
            if line.strip().startswith(("[STEP_", "Step ", "Paso ")):
                steps.append(line.replace("[STEP_", "").replace("]", "").strip())
        return steps[:10]  # Max 10 steps

    def _parse_quiz_questions(self, content: str, num_q: int) -> List[dict]:
        """Parse quiz questions from response"""
        questions = []
        lines = content.split("\n")

        current_q = None
        for line in lines:
            if line.startswith("Question:"):
                if current_q:
                    questions.append(current_q)
                current_q = {"question": line.replace("Question:", "").strip(), "options": []}
            elif line.startswith(("A)", "B)", "C)", "D)")) and current_q:
                current_q["options"].append(line.strip())
            elif line.startswith("Correct:") and current_q:
                current_q["correct_answer"] = 0  # Default to A

        if current_q:
            questions.append(current_q)

        return questions[:num_q]

    def _extract_summary(self, content: str) -> str:
        """Extract lesson summary (first paragraph)"""
        lines = content.split("\n")
        summary = ""
        for line in lines[:5]:
            if line.strip():
                summary += line + " "
                if len(summary) > 100:
                    break
        return summary.strip()[:200]

    def _extract_examples(self, content: str) -> List[str]:
        """Extract example sections"""
        examples = []
        in_example = False
        for line in content.split("\n"):
            if "[EXAMPLE]" in line or "ejemplo" in line.lower():
                in_example = True
            elif in_example and line.strip():
                examples.append(line.strip())
                if len(examples) > 3:
                    break
        return examples

    def _extract_references(self, content: str) -> List[str]:
        """Extract reference citations"""
        refs = []
        in_refs = False
        for line in content.split("\n"):
            if "[REFERENCES" in line or "Fuente:" in line or "Source:" in line:
                in_refs = True
            elif in_refs and line.strip():
                if "http" in line or any(x in line for x in ["TOGAF", "ISO", "DAMA", "NIST"]):
                    refs.append(line.strip())
        return refs

    def _extract_setup(self, content: str) -> str:
        """Extract lab setup instructions"""
        for line in content.split("\n"):
            if "[SETUP]" in line:
                return content.split("[SETUP]")[1].split("[")[0].strip()
        return "1. Clone repository\n2. Install dependencies\n3. Configure environment"

    def _extract_validation_criteria(self, content: str) -> List[str]:
        """Extract lab validation criteria"""
        criteria = []
        in_validation = False
        for line in content.split("\n"):
            if "[VALIDATION]" in line:
                in_validation = True
            elif in_validation and line.strip() and not line.startswith("["):
                criteria.append(line.strip())
                if len(criteria) > 5:
                    break
        return criteria if criteria else ["All steps completed", "Code runs without errors"]

    def _requires_legal_review(self, content: str) -> bool:
        """Check if content needs legal review"""
        legal_keywords = ["ley", "regulación", "cumplimiento", "privacidad", "21.719", "iso 27"]
        return any(kw in content.lower() for kw in legal_keywords)

    def _infer_tools(self, topic: str) -> List[str]:
        """Infer required tools from topic"""
        tools_map = {
            "cloud": ["AWS", "GCP", "Azure CLI"],
            "data": ["SQL", "dbt", "Spark"],
            "architecture": ["Draw.io", "Mermaid", "Structurizr"],
            "code": ["Python", "Git", "Docker"],
            "security": ["OpenSSL", "HashiCorp Vault"],
        }
        tools = []
        for key, vals in tools_map.items():
            if key in topic.lower():
                tools.extend(vals)
        return tools if tools else ["Python", "Git"]

    def __repr__(self) -> str:
        return f"<InstructorAgent - {self.model_name}>"
