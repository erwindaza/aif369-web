"""
LangGraph Orchestrator for Multi-Agent Platform
Coordinates Sales Concierge → Discovery → Scorecard flow
"""

import json
import uuid
from datetime import datetime
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import anthropic

from config import (
    MODEL,
    TEMPERATURE,
    PlatformState,
    CONCIERGE_SYSTEM,
    DISCOVERY_SYSTEM,
    SCORECARD_SYSTEM,
)

client = anthropic.Anthropic()
memory = MemorySaver()


class AgentOrchestrator:
    """Manages multi-agent flow for sales discovery"""

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self):
        """Build LangGraph workflow"""
        workflow = StateGraph(PlatformState)

        # Add nodes
        workflow.add_node("concierge", self._concierge_agent)
        workflow.add_node("discovery", self._discovery_agent)
        workflow.add_node("scorecard", self._scorecard_agent)
        workflow.add_node("summarize", self._summarize_engagement)

        # Add edges with routing logic
        workflow.add_conditional_edges(
            "concierge",
            self._route_from_concierge,
            {
                "discovery": "discovery",
                "end": END,
            },
        )

        workflow.add_conditional_edges(
            "discovery",
            self._route_from_discovery,
            {
                "scorecard": "scorecard",
                "end": END,
            },
        )

        workflow.add_edge("scorecard", "summarize")
        workflow.add_edge("summarize", END)

        # Set entry point
        workflow.set_entry_point("concierge")

        return workflow.compile(checkpointer=memory)

    def _concierge_agent(self, state: PlatformState) -> PlatformState:
        """Sales Concierge: Initial greeting and profiling"""

        # If this is first turn, send greeting
        if not state["messages"]:
            greeting = """¡Hola! Soy el Sales Concierge de AIF369.

Estamos especializados en transformación con IA para empresas en LATAM. Nuestro objetivo es entender tu contexto y mostrar exactamente cómo podemos ayudarte.

Para empezar, ¿cuál es tu nombre y en qué empresa trabajas?"""

            state["messages"].append(
                {"role": "assistant", "content": greeting}
            )
            state["current_agent"] = "concierge"
            return state

        # Get latest user message
        user_msg = state["messages"][-1]["content"]

        # Extract info using Claude
        extraction_prompt = f"""Analiza este mensaje del cliente y extrae:
- nombre
- empresa
- rol (si menciona)
- señal de urgencia (baja, media, alta)
- presupuesto estimado (si menciona)

Mensaje: "{user_msg}"

Responde en JSON."""

        extraction_response = client.messages.create(
            model=MODEL,
            max_tokens=500,
            messages=[
                {"role": "user", "content": extraction_prompt}
            ],
        )

        try:
            extracted = json.loads(extraction_response.content[0].text)
            if extracted.get("nombre"):
                state["name"] = extracted["nombre"]
            if extracted.get("empresa"):
                state["company"] = extracted["empresa"]
            if extracted.get("rol"):
                state["role"] = extracted["rol"]
            if extracted.get("presupuesto_estimado"):
                state["budget_estimate"] = extracted["presupuesto_estimado"]
        except:
            pass

        # Generate Concierge response
        concierge_prompt = f"""Eres el Sales Concierge de AIF369.

Context:
- Nombre cliente: {state.get('name', 'Unknown')}
- Empresa: {state.get('company', 'Unknown')}
- Rol: {state.get('role', 'Unknown')}

Último mensaje del cliente: "{user_msg}"

Tu tarea:
1. Si falta nombre/empresa, pide esos datos
2. Si ya tiene esos datos, haz una pregunta de warm-up sobre por qué nos contactó
3. Mantén tono conversacional y empático
4. Máximo 2-3 oraciones

Responde solo el mensaje, sin explicaciones extras."""

        response = client.messages.create(
            model=MODEL,
            max_tokens=300,
            temperature=TEMPERATURE,
            system=CONCIERGE_SYSTEM,
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in state["messages"]
            ] + [{"role": "user", "content": concierge_prompt}],
        )

        assistant_msg = response.content[0].text
        state["messages"].append(
            {"role": "assistant", "content": assistant_msg}
        )
        state["current_agent"] = "concierge"

        return state

    def _discovery_agent(self, state: PlatformState) -> PlatformState:
        """Discovery: Deep dive into business context"""

        if state["current_agent"] != "discovery":
            # First turn in discovery
            discovery_opener = f"""Perfecto, {state.get('name', 'amigo')}. Ahora voy a hacer algunas preguntas para entender mejor tu situación.

Pregunta 1 de 5:
¿Qué tan maduro consideras el programa de IA en {state.get('company', 'tu empresa')} hoy? (escala 1-10, donde 1 es "no tenemos IA" y 10 es "somos líderes en IA")"""

            state["messages"].append(
                {"role": "assistant", "content": discovery_opener}
            )
            state["current_agent"] = "discovery"
            return state

        # Get user response and ask next discovery question
        user_msg = state["messages"][-1]["content"]

        # Extract maturity score
        try:
            maturity = int("".join(filter(str.isdigit, user_msg.split()[0])))
            state["current_ai_maturity"] = min(10, max(1, maturity))
        except:
            pass

        # Determine which discovery question to ask next
        discovery_turn = len([m for m in state["messages"] if m["role"] == "assistant" and "Pregunta" in m["content"]])

        questions = [
            "¿Cuáles son tus 3 procesos más críticos que dependen de datos? (ej: finanzas, operaciones, ventas)",
            "¿Cuál es el mayor dolor que tienes hoy? (costos, velocidad, errores, compliance)",
            "¿Cuál debería ser tu prioridad número 1 en IA para los próximos 6 meses?",
            "¿Tienes equipo de datos o datos disponibles para trabajar? ¿Qué tan limpios están?",
        ]

        if discovery_turn < len(questions):
            next_q = f"Pregunta {discovery_turn + 1} de 5:\n{questions[discovery_turn - 1]}"
        else:
            next_q = "Perfecto. Creo que tengo suficiente contexto. Vamos a hacer tu AI Scorecard 369 para evaluar tu madurez real en IA."

        state["messages"].append(
            {"role": "assistant", "content": next_q}
        )
        state["current_agent"] = "discovery"

        return state

    def _scorecard_agent(self, state: PlatformState) -> PlatformState:
        """AI Scorecard 369: Evaluate maturity across 9 dimensions"""

        if state["current_agent"] != "scorecard":
            # First turn: explain scorecard
            opener = """Ahora voy a evaluar tu madurez en IA usando el AI Scorecard 369.

Este evalúa 9 dimensiones clave. Para cada una, te haré 1-2 preguntas rápidas.

Dimensión 1: AI Strategy
¿Tienes una visión clara de cómo la IA debería transformar tu negocio en los próximos 2 años?"""

            state["messages"].append(
                {"role": "assistant", "content": opener}
            )
            state["current_agent"] = "scorecard"
            return state

        # Evaluate based on conversation so far
        user_msg = state["messages"][-1]["content"].lower()

        # Simple scoring logic (will be enhanced with Claude eval)
        scorecard_scores = {
            "AI Strategy": self._score_dimension(user_msg, ["vision", "roadmap", "clear"]),
            "AI Governance": self._score_dimension(user_msg, ["governance", "control", "committee"]),
            "Risk Management": self._score_dimension(user_msg, ["risk", "seguridad", "compliance"]),
            "Data Quality": self._score_dimension(user_msg, ["datos", "clean", "limpios"]),
            "AI Factory": self._score_dimension(user_msg, ["build", "deploy", "producción"]),
            "Observability": self._score_dimension(user_msg, ["monitor", "métricas", "observability"]),
            "Ethics & Responsible AI": self._score_dimension(user_msg, ["ethics", "ética", "bias"]),
            "Regulation & Compliance": self._score_dimension(user_msg, ["21.719", "GDPR", "compliance", "regulación"]),
            "Talent & Culture": self._score_dimension(user_msg, ["team", "equipo", "talent", "training"]),
        }

        state["scorecard_scores"] = scorecard_scores
        overall = sum(scorecard_scores.values()) / len(scorecard_scores)
        state["overall_maturity"] = int(overall)

        # Generate summary
        summary = f"""✅ RESULTADOS - AI SCORECARD 369

Madurez general: {state['overall_maturity']}/10

Dimensiones:
{chr(10).join([f"• {dim}: {score}/10" for dim, score in scorecard_scores.items()])}

Interpretación:
{self._interpret_scorecard(state['overall_maturity'])}

Próximo paso: Vamos a diseñar una arquitectura y calcular ROI específicamente para ti."""

        state["messages"].append(
            {"role": "assistant", "content": summary}
        )
        state["current_agent"] = "scorecard"
        state["stage"] = "scoring_complete"

        return state

    def _summarize_engagement(self, state: PlatformState) -> PlatformState:
        """Generate executive summary"""

        summary = f"""
RESUMEN DE ENGAGEMENT - {state.get('company', 'N/A')}

Cliente: {state.get('name', 'N/A')}
Email: {state.get('email', 'N/A')}
Rol: {state.get('role', 'N/A')}

PERFIL DESCUBIERTO:
- Madurez IA Actual: {state.get('current_ai_maturity', 0)}/10
- Procesos Críticos: {', '.join(state.get('critical_processes', []))}
- Dolores Principales: {', '.join(state.get('main_pains', []))}

AI SCORECARD 369:
- Resultado General: {state.get('overall_maturity', 0)}/10
- Fortalezas: [Top 3 dimensiones altas]
- Brechas: [Top 3 dimensiones bajas]

SIGUIENTE FASE:
- Architecture Design
- ROI Calculation
- Proposal Generation
"""

        state["messages"].append(
            {"role": "system", "content": summary}
        )
        state["stage"] = "ready_for_proposal"

        return state

    def _route_from_concierge(self, state: PlatformState) -> Literal["discovery", "end"]:
        """Decide if we have enough info to move to discovery"""
        has_name = bool(state.get("name"))
        has_email = bool(state.get("email"))
        turn_count = len(state["messages"])

        # Move to discovery after 3+ exchanges and we have name
        if turn_count >= 6 and has_name:
            return "discovery"
        return "concierge"

    def _route_from_discovery(self, state: PlatformState) -> Literal["scorecard", "end"]:
        """Decide if we have enough info for scorecard"""
        discovery_turns = len([m for m in state["messages"] if "Pregunta" in m.get("content", "")])

        # After 5 discovery questions, move to scorecard
        if discovery_turns >= 5:
            return "scorecard"
        return "discovery"

    def _score_dimension(self, text: str, keywords: list[str]) -> int:
        """Simple keyword-based scoring (will use Claude for real eval)"""
        matches = sum(1 for kw in keywords if kw.lower() in text.lower())
        return min(10, max(1, matches * 2))

    def _interpret_scorecard(self, score: int) -> str:
        """Interpret overall scorecard score"""
        if score >= 8:
            return "🚀 Avanzado: Ya tienes bases sólidas. Foco en escalar y optimizar."
        elif score >= 6:
            return "📈 Intermedio: Buen progreso. Necesitas estructura y governance."
        elif score >= 4:
            return "🟡 Básico: Iniciando. Hay oportunidad grande de crecimiento."
        else:
            return "⚠️ Inicial: Estás en el punto de partida. Es el mejor momento para empezar."

    async def run_conversation(self, session_id: str, user_input: str, current_state: dict) -> dict:
        """Run one turn of conversation"""

        # Initialize state if needed
        if not current_state:
            current_state = {
                "session_id": session_id or str(uuid.uuid4()),
                "conversation_id": str(uuid.uuid4()),
                "name": "",
                "email": "",
                "company": "",
                "role": "",
                "phone": "",
                "industry": "",
                "company_size": "",
                "current_ai_maturity": 0,
                "critical_processes": [],
                "main_pains": [],
                "priorities": [],
                "budget_estimate": "",
                "scorecard_scores": {},
                "scorecard_summary": "",
                "overall_maturity": 0,
                "messages": [],
                "current_agent": "",
                "created_at": datetime.now().isoformat(),
                "last_update": datetime.now().isoformat(),
                "stage": "discovery",
            }

        # Add user message
        current_state["messages"].append({"role": "user", "content": user_input})

        # Run through graph
        result = self.graph.invoke(current_state)

        return result


# Initialize orchestrator
orchestrator = AgentOrchestrator()
