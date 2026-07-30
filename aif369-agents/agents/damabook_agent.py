"""DAMABOOK Worker Agent - Data Governance and Ley 21.719 specialist"""
import asyncio
import time
from typing import Any, Dict
import ollama
from models import Task
from agents.base import BaseAgent
from config import ConfigManager
from tools import WhatsAppTool, InterAgentEventTool
from tools.whatsapp_formatter import WhatsAppFormatter
from core import QueueManager


class DamabookAgent(BaseAgent):
    """
    DAMABOOK Worker Agent
    Specializes in data governance and Ley 21.719 compliance.

    Responsibilities:
    - Ley 21.719 compliance (Protección de Datos Personales - Chile)
    - Data governance strategy and implementation
    - Data quality and metadata management
    - Multimodal document analysis (with Kimi K3)

    Ley 21.719 Knowledge:
    - Consentimiento explícito para procesamiento de datos
    - Derechos del titular: acceso, rectificación, supresión, oposición
    - Protección de datos sensibles
    - Auditorías y reportes
    - Responsable de protección de datos (DPO equivalent)
    - Cumplimiento obligatorio: 18 meses desde promulgación

    Services:
    - Data Governance Audit: $3k USD
    - Ley 21.719 Compliance Plan: $5k USD
    - Data Quality Framework: $4k USD
    - Ongoing Support: $2k USD/month
    """

    def __init__(self):
        super().__init__(agent_id="damabook", model_name="kimi-k3:cloud")
        self.config = ConfigManager.get_instance()

        # Try Kimi K3 first, fallback to Mistral
        try:
            self.client = ollama.Client(host=self.config.ollama_host)
            self.model_name = "kimi-k3:cloud"
        except:
            self.logger.warning("Kimi K3 not available, using mistral:7b fallback")
            self.client = ollama.Client(host=self.config.ollama_host)
            self.model_name = "mistral:7b"

        # Tools
        self.whatsapp_tool = WhatsAppTool()
        self.queue_manager = QueueManager.get_instance()
        self.inter_agent_tool = InterAgentEventTool(self.queue_manager)

        # LEY 21.719 Knowledge Base
        self.ley_21719_info = {
            "nombre": "Ley de Protección de Datos Personales (Ley 21.719)",
            "pais": "Chile",
            "promulgacion": "2022",
            "entrada_vigencia": "2023 (18 meses para cumplimiento)",
            "equivalente": "GDPR Europeo",
            "aplicacion": "Organizaciones públicas y privadas que procesen datos personales",
        }

        self.derechos_titular = [
            "Acceso": "Derecho a acceder a sus datos personales",
            "Rectificación": "Corregir datos inexactos",
            "Supresión": "Eliminación de datos (derecho al olvido)",
            "Limitación": "Limitar el procesamiento",
            "Oposición": "Rechazar ciertos tipos de procesamiento",
            "Portabilidad": "Transferir datos a otra organización",
        ]

        self.obligaciones = [
            "Obtener consentimiento explícito",
            "Documentar bases legales de procesamiento",
            "Implementar medidas de seguridad",
            "Realizar evaluaciones de impacto (DPIA)",
            "Reportar brechas de datos",
            "Designar responsable de protección de datos",
            "Mantener registros de procesamiento",
            "Documentar políticas de privacidad",
        ]

        self.servicios = {
            "audit": {
                "name": "Data Governance Audit",
                "price": 3000,
                "duration": "3 semanas",
                "includes": [
                    "Análisis de datos actuales",
                    "Mapeo de procesamiento",
                    "Evaluación Ley 21.719",
                    "Reporte de gaps",
                ],
            },
            "compliance": {
                "name": "Ley 21.719 Compliance Plan",
                "price": 5000,
                "duration": "1 mes",
                "includes": [
                    "Plan de acción detallado",
                    "Políticas de privacidad",
                    "Consentimiento templates",
                    "Procedimientos de seguridad",
                ],
            },
            "quality": {
                "name": "Data Quality Framework",
                "price": 4000,
                "duration": "4 semanas",
                "includes": [
                    "Framework de calidad",
                    "Métricas de datos",
                    "Validación y limpieza",
                    "Monitoreo continuo",
                ],
            },
            "support": {
                "name": "Ongoing Support & Monitoring",
                "price": 2000,
                "duration": "Monthly",
                "includes": [
                    "Monitoreo de cumplimiento",
                    "Actualizaciones normativas",
                    "Soporte técnico",
                    "Reportes mensuales",
                ],
            },
        }

    async def _process(self, task: Task) -> dict:
        """
        Process data governance and compliance inquiry

        Flow:
        1. Understand data governance need
        2. Assess Ley 21.719 impact
        3. Recommend compliance path
        4. Offer governance services
        """
        payload = task.payload
        customer_query = payload.get("message", "")
        customer_phone = payload.get("customer_phone")
        document_data = payload.get("document")  # Multimodal: image/document

        # Build specialized prompt
        prompt = self._build_governance_prompt(customer_query, document_data)

        try:
            # Use appropriate model
            model_to_use = self.model_name

            response = await asyncio.to_thread(
                self.client.generate,
                model=model_to_use,
                prompt=prompt,
                stream=False,
                options={"temperature": 0.6, "num_predict": 500},
            )

            output_text = response.get("response", "")

            # Check if needs escalation
            should_escalate = self._check_escalation_needed(customer_query)

            result = {
                "status": "success",
                "response": output_text,
                "model_used": model_to_use,
                "compliance_areas": self._extract_compliance_areas(output_text),
                "services_mentioned": self._extract_services(output_text),
                "ley_21719_relevant": self._is_ley_21719_relevant(customer_query),
                "agent": "damabook",
                "escalate_to_legal": should_escalate,
            }

            # If legal review needed, escalate
            if should_escalate:
                self.logger.info("Escalating to LEGAL agent for formal review")
                event_result = await self.inter_agent_tool.execute(
                    event_type="request_legal_review",
                    target_agent="legal",
                    data={
                        "customer_query": customer_query,
                        "governance_assessment": output_text,
                        "ley_21719_impact": "high",
                    },
                    source_agent="damabook",
                    wait_for_result=False,
                )
                result["escalation_event"] = event_result

            # Send WhatsApp if available
            if customer_phone:
                formatted_msg = WhatsAppFormatter.damabook_response(
                    ley_21719_relevant=self._is_ley_21719_relevant(customer_query),
                    compliance_areas=self._extract_compliance_areas(output_text),
                    escalation_to_legal=should_escalate,
                )
                await self.whatsapp_tool.execute(
                    phone=customer_phone,
                    message=formatted_msg,
                )

            return result

        except Exception as e:
            self.logger.error(f"DAMABOOK agent error: {e}")
            raise

    def _build_governance_prompt(self, customer_query: str, document_data: str = None) -> str:
        """Build data governance prompt with Ley 21.719 knowledge"""

        derechos_text = "\n".join([f"- {d}: {desc}" for d, desc in self.derechos_titular.items()])
        obligaciones_text = "\n".join([f"- {o}" for o in self.obligaciones])
        servicios_text = "\n".join(
            [f"- {s['name']}: ${s['price']} ({s['duration']})" for s in self.servicios.values()]
        )

        document_context = ""
        if document_data:
            document_context = f"\n\nDOCUMENTO A ANALIZAR (multimodal):\n{document_data}"

        return f"""Eres DAMABOOK - Experto en Gobernanza de Datos y Ley 21.719 (Protección de Datos Personales Chile).

LEY 21.719 - DERECHOS DEL TITULAR:
{derechos_text}

LEY 21.719 - OBLIGACIONES ORGANIZACIONALES:
{obligaciones_text}

SERVICIOS OFRECIDOS:
{servicios_text}

CLIENTE PREGUNTA/NECESIDAD:
{customer_query}{document_context}

Tu objetivo:
1. Evaluar impacto de Ley 21.719
2. Identificar gaps de cumplimiento
3. Proponer plan de gobernanza
4. Explicar derechos del titular
5. Recomendar servicios específicos

IMPORTANTE:
- Si es pregunta legal compleja, sugiere escalación a LEGAL
- Si menciona documento/política, analiza multimodal
- Sé específico sobre cumplimiento de Ley 21.719

RESPUESTA (profesional, detallada, máx 250 palabras):"""

    def _is_ley_21719_relevant(self, query: str) -> bool:
        """Check if query is about Ley 21.719"""
        keywords = ["21.719", "ley protección", "datos personales", "privacidad", "gdpr", "cumplimiento"]
        return any(kw in query.lower() for kw in keywords)

    def _check_escalation_needed(self, query: str) -> bool:
        """Check if should escalate to LEGAL agent"""
        escalation_keywords = [
            "sanciones",
            "multas",
            "responsabilidad",
            "demanda",
            "litigios",
            "interpretación legal",
            "tribunal",
        ]
        return any(kw in query.lower() for kw in escalation_keywords)

    def _extract_compliance_areas(self, response: str) -> list:
        """Extract compliance areas mentioned"""
        areas = []
        area_keywords = {
            "consentimiento": "Consent Management",
            "seguridad": "Security",
            "auditoría": "Audit",
            "derechos": "Data Subject Rights",
            "brechas": "Breach Notification",
            "dpia": "Impact Assessment",
        }
        for keyword, area in area_keywords.items():
            if keyword in response.lower():
                areas.append(area)
        return areas

    def _extract_services(self, response: str) -> list:
        """Extract service mentions"""
        mentioned = []
        for key, service in self.servicios.items():
            if key.lower() in response.lower() or service["name"].lower() in response.lower():
                mentioned.append({"key": key, "name": service["name"], "price": service["price"]})
        return mentioned

    def __repr__(self) -> str:
        return f"<DamabookAgent - {self.model_name}>"
