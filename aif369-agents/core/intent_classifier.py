"""Intent Classifier - Detects user intent and routes to correct agent"""
from typing import Dict, Tuple
from core import LoggerManager


class IntentClassifier:
    """
    Classify customer intent to route to correct agent

    Intents:
    - VENTAS: Buy course, pricing, product info
    - CAIO: Enterprise consulting, implementation, architecture
    - LEGAL: GDPR, data protection, compliance
    - DAMABOOK: Data governance, quality
    - SUPPORT: General questions, help
    """

    def __init__(self):
        self.logger = LoggerManager.get_logger("IntentClassifier")

        # Keywords for each intent
        self.ventas_keywords = [
            "comprar",
            "precio",
            "costo",
            "curso",
            "taller",
            "inscribir",
            "aprender",
            "pagar",
            "oferta",
            "promoción",
            "materials",
            "video",
            "certificado",
            "cuanto cuesta",
            "disponible",
        ]

        self.caio_keywords = [
            "implementar",
            "empresa",
            "consultoría",
            "proyecto",
            "arquitectura",
            "producción",
            "integración",
            "equipo",
            "presupuesto",
            "asesoría",
            "estrategia",
            "roadmap",
            "customizado",
            "solución",
            "roi",
            "negocio",
        ]

        self.legal_keywords = [
            "gdpr",
            "protección datos",
            "privacidad",
            "ley",
            "legal",
            "cumplimiento",
            "consentimiento",
            "términos",
            "condiciones",
            "derechos",
            "rgpd",
        ]

        self.damabook_keywords = [
            "datos",
            "gobernanza",
            "calidad datos",
            "governance",
            "metadata",
            "lineage",
            "catálogo",
            "política",
            "retención",
            "clasificación",
        ]

    def classify(self, query: str) -> Tuple[str, float]:
        """
        Classify intent from query

        Returns:
            (agent_name, confidence_score)
            agent_name: "ventas", "caio", "legal", "damabook", "support"
            confidence_score: 0.0-1.0
        """
        query_lower = query.lower()

        # Score each intent
        scores = {
            "ventas": self._score_intent(query_lower, self.ventas_keywords),
            "caio": self._score_intent(query_lower, self.caio_keywords),
            "legal": self._score_intent(query_lower, self.legal_keywords),
            "damabook": self._score_intent(query_lower, self.damabook_keywords),
        }

        # Get best match
        best_agent = max(scores, key=scores.get)
        best_score = scores[best_agent]

        # If confidence too low, return support
        if best_score < 0.2:
            best_agent = "support"
            best_score = 0.0

        self.logger.info(
            f"Classified: '{query[:50]}...' → {best_agent} (score={best_score:.2f})"
        )

        return best_agent, best_score

    def _score_intent(self, query: str, keywords: list) -> float:
        """Score how well query matches intent"""
        if not keywords:
            return 0.0

        matches = sum(1 for keyword in keywords if keyword in query)
        return min(1.0, matches / len(keywords))

    def __repr__(self) -> str:
        return "<IntentClassifier>"
