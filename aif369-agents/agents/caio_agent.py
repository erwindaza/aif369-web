"""CAIO Agent - Specializes in AI consulting"""
import asyncio
import time
from typing import Any, Dict
import ollama
from models import Task
from agents.base import BaseAgent
from config import ConfigManager
from tools import WhatsAppTool, InterAgentEventTool
from core import QueueManager


class CAIOAgent(BaseAgent):
    """
    Specialized CAIO Agent (Chief AI Officer)
    - Enterprise AI consulting
    - Strategy, architecture, implementation
    - ROI analysis, case studies
    - Escalation from sales

    Services:
    - AI Audit: $5k USD
    - Strategy & Design: $10k USD
    - Implementation: $15k-$50k USD
    - Training & Support: $5k USD/month
    """

    def __init__(self):
        super().__init__(agent_id="caio", model_name="mistral:7b")
        self.config = ConfigManager.get_instance()
        self.client = ollama.Client(host=self.config.ollama_host)

        # Tools
        self.whatsapp_tool = WhatsAppTool()
        self.queue_manager = QueueManager.get_instance()
        self.inter_agent_tool = InterAgentEventTool(self.queue_manager)

        # Service offerings
        self.services = {
            "audit": {
                "name": "AI Audit",
                "price": 5000,
                "duration": "2-3 weeks",
                "includes": [
                    "Current state assessment",
                    "Roadmap",
                    "Risk analysis",
                ],
            },
            "strategy": {
                "name": "AI Strategy & Design",
                "price": 10000,
                "duration": "1 month",
                "includes": [
                    "Architecture design",
                    "Technology selection",
                    "Implementation plan",
                ],
            },
            "implementation": {
                "name": "AI Implementation",
                "price": 25000,
                "duration": "3-6 months",
                "includes": [
                    "Development",
                    "Integration",
                    "Testing",
                    "Deployment",
                ],
            },
            "training": {
                "name": "Team Training & Support",
                "price": 5000,
                "duration": "Ongoing",
                "includes": [
                    "Team training",
                    "Monthly support",
                    "Optimization",
                ],
            },
        }

    async def _process(self, task: Task) -> dict:
        """
        Process consulting inquiry

        Flow:
        1. Understand enterprise needs
        2. Recommend consulting path
        3. Discuss investment and ROI
        4. Schedule discovery call
        """
        payload = task.payload
        customer_query = payload.get("message") or payload.get("initial_context", "")
        customer_phone = payload.get("customer_phone")
        is_escalation = payload.get("type") == "inter_agent_event"

        # Build consulting prompt
        prompt = self._build_consulting_prompt(customer_query, is_escalation)

        try:
            response = await asyncio.to_thread(
                self.client.generate,
                model=self.model_name,
                prompt=prompt,
                stream=False,
                options={"temperature": 0.6, "num_predict": 400},
            )

            output_text = response.get("response", "")

            result = {
                "status": "success",
                "response": output_text,
                "services_mentioned": self._extract_services(output_text),
                "next_step": "Schedule discovery call",
                "agent": "caio",
                "is_escalation": is_escalation,
            }

            # Send WhatsApp if available
            if customer_phone:
                await self.whatsapp_tool.execute(
                    phone=customer_phone,
                    message=f"💼 Consultoría IA - {output_text[:80]}...\n\nVamos a agendar una llamada.",
                )

            return result

        except Exception as e:
            self.logger.error(f"CAIO agent error: {e}")
            raise

    def _build_consulting_prompt(self, customer_query: str, is_escalation: bool) -> str:
        """Build consulting prompt with services knowledge"""
        services_text = "\n".join(
            [
                f"- {s['name']}: ${s['price']} ({s['duration']})"
                for s in self.services.values()
            ]
        )

        escalation_context = (
            "NOTA: Este cliente fue escalado desde VENTAS. "
            "Necesita consultoría/implementación, no solo cursos.\n"
        )

        return f"""Eres un Chief AI Officer (CAIO) - Experto en consultoría empresarial de IA.

SERVICIOS OFRECIDOS:
{services_text}

{escalation_context if is_escalation else ""}

CLIENTE PREGUNTA/NECESIDAD: {customer_query}

Tu objetivo:
1. Entender la necesidad empresarial profundamente
2. Proponer solución específica
3. Explicar ROI y beneficios
4. Sugerir próximos pasos
5. Indicar inversión esperada

RESPUESTA (profesional, detallada, máx 200 palabras):"""

    def _extract_services(self, response: str) -> list:
        """Extract service mentions from response"""
        mentioned = []
        for key, service in self.services.items():
            if key.lower() in response.lower() or service["name"].lower() in response.lower():
                mentioned.append(
                    {"key": key, "name": service["name"], "price": service["price"]}
                )
        return mentioned

    def __repr__(self) -> str:
        return "<CAIOAgent - Chief AI Officer>"
