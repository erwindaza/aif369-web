"""VENTAS Worker Agent - Sells courses and workshops"""
import asyncio
import time
from typing import Any, Dict
import ollama
from models import Task
from agents.base import BaseAgent
from config import ConfigManager
from tools import WhatsAppTool, InterAgentEventTool
from core import QueueManager


class VentasAgent(BaseAgent):
    """
    VENTAS Worker Agent
    Specializes in selling courses, workshops, and products.

    Responsibilities:
    - Sells courses, workshops, handles product queries
    - Knows pricing, features, testimonials
    - Can close sales or escalate to CAIO for consulting

    Knowledge Base:
    - Curso Agentes: $12.99 USD (2h video, materials)
    - Curso RAG: $14.99 USD (3h video, labs)
    - Curso LLMs: $11.99 USD (2.5h video)
    - Talleres Prácticos: $299 USD (5 days, online)
    - Asesoría CAIO: starts at $15k USD
    """

    def __init__(self):
        super().__init__(agent_id="ventas", model_name="mistral:7b")
        self.config = ConfigManager.get_instance()
        self.client = ollama.Client(host=self.config.ollama_host)

        # Tools
        self.whatsapp_tool = WhatsAppTool()
        self.queue_manager = QueueManager.get_instance()
        self.inter_agent_tool = InterAgentEventTool(self.queue_manager)

        # Product catalog
        self.products = {
            "agentes": {
                "name": "Curso: Agentes IA",
                "price": 12.99,
                "duration": "2 horas",
                "includes": ["Videos", "Materiales PDF", "Código fuente"],
                "level": "Principiante",
            },
            "rag": {
                "name": "Curso: RAG Systems",
                "price": 14.99,
                "duration": "3 horas",
                "includes": ["Videos", "Labs prácticos", "Documentación"],
                "level": "Intermedio",
            },
            "llms": {
                "name": "Curso: LLM Fundamentals",
                "price": 11.99,
                "duration": "2.5 horas",
                "includes": ["Videos", "Ejemplos", "Recursos"],
                "level": "Principiante",
            },
            "taller": {
                "name": "Taller Práctico: Agentes en Producción",
                "price": 299.00,
                "duration": "5 días",
                "includes": ["Sesiones en vivo", "Mentoring", "Proyecto final"],
                "level": "Avanzado",
            },
        }

    async def _process(self, task: Task) -> dict:
        """
        Process sales inquiry

        Flow:
        1. Understand customer need
        2. Recommend products
        3. Handle objections
        4. Close or escalate to CAIO
        """
        payload = task.payload
        customer_query = payload.get("message", "")
        customer_phone = payload.get("customer_phone")

        # Build prompt with product knowledge
        prompt = self._build_sales_prompt(customer_query)

        try:
            response = await asyncio.to_thread(
                self.client.generate,
                model=self.model_name,
                prompt=prompt,
                stream=False,
                options={"temperature": 0.7, "num_predict": 300},
            )

            output_text = response.get("response", "")

            # Detect if should escalate to CAIO
            should_escalate = self._check_escalation(customer_query)

            result = {
                "status": "success",
                "response": output_text,
                "products_mentioned": self._extract_products(output_text),
                "escalate_to_caio": should_escalate,
                "agent": "ventas",
            }

            # If escalate to CAIO
            if should_escalate:
                self.logger.info("Escalating to CAIO agent")
                event_result = await self.inter_agent_tool.execute(
                    event_type="request_consulting",
                    target_agent="caio",
                    data={
                        "customer_query": customer_query,
                        "initial_context": output_text,
                    },
                    source_agent="ventas",
                    wait_for_result=False,
                )
                result["escalation_event"] = event_result

            # Send WhatsApp if customer phone provided
            if customer_phone and not should_escalate:
                await self.whatsapp_tool.execute(
                    phone=customer_phone,
                    message=f"🎓 {output_text[:100]}...",
                )

            return result

        except Exception as e:
            self.logger.error(f"Ventas agent error: {e}")
            raise

    def _build_sales_prompt(self, customer_query: str) -> str:
        """Build prompt with sales knowledge and products"""
        products_text = "\n".join(
            [
                f"- {p['name']}: ${p['price']} ({p['duration']})"
                for p in self.products.values()
            ]
        )

        return f"""Eres un agente de ventas especializado en cursos y talleres de IA.

PRODUCTOS DISPONIBLES:
{products_text}

CLIENTE PREGUNTA: {customer_query}

Tu objetivo:
1. Entender qué necesita el cliente
2. Recomendar productos específicos
3. Explicar beneficios y valor
4. Si pregunta sobre implementación/consultoría empresarial, sugiere asesoría CAIO ($15k USD+)

RESPUESTA (amigable, concisa, máx 150 palabras):"""

    def _check_escalation(self, query: str) -> bool:
        """Check if should escalate to CAIO (consulting)"""
        escalation_keywords = [
            "implementar",
            "empresa",
            "consultoría",
            "proyecto",
            "arquitectura",
            "producción",
            "integración",
            "equipo",
            "presupuesto",
        ]

        return any(keyword in query.lower() for keyword in escalation_keywords)

    def _extract_products(self, response: str) -> list:
        """Extract product mentions from response"""
        mentioned = []
        for key, product in self.products.items():
            if key.lower() in response.lower() or product["name"].lower() in response.lower():
                mentioned.append({"key": key, "name": product["name"], "price": product["price"]})
        return mentioned

    def __repr__(self) -> str:
        return "<VentasAgent - Mistral 7B>"
