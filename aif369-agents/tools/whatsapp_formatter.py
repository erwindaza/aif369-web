"""WhatsApp message formatter for professional, formatted responses"""


class WhatsAppFormatter:
    """Formats responses for WhatsApp with good UX and clear CTAs"""

    # Base URLs
    SITE_URL = "https://aif369.com"
    CHECKOUT_URL = f"{SITE_URL}/checkout"
    CONTACT_URL = f"{SITE_URL}/contact"

    @staticmethod
    def ventas_response(products_mentioned: list, has_escalation: bool = False) -> str:
        """Format VENTAS agent response for WhatsApp"""
        if has_escalation:
            return (
                "🎓 Veo que necesitas implementar esto en tu empresa.\n\n"
                "Te estoy conectando con nuestro especialista en Consultoría IA "
                "(Chief AI Officer) para una evaluación personalizada.\n\n"
                "💼 *Espera su contacto en los próximos minutos* ⏳"
            )

        lines = ["🎓 *CURSOS IA - OPCIONES DISPONIBLES*\n"]

        if not products_mentioned:
            lines.extend([
                "💡 Ofrecemos 4 programas profesionales:\n",
                "1️⃣ *Curso: Agentes IA* - $12.99 USD (2h video)",
                "2️⃣ *Curso: RAG Systems* - $14.99 USD (3h video)",
                "3️⃣ *Curso: LLM Fundamentals* - $11.99 USD (2.5h video)",
                "4️⃣ *Taller Práctico* - $299 USD (5 días, mentoring)\n",
            ])
        else:
            for product in products_mentioned:
                lines.append(f"✅ {product['name']} - ${product['price']} USD")
            lines.append("")

        lines.extend([
            "👉 *COMPRA AHORA:*",
            f"{WhatsAppFormatter.CHECKOUT_URL}\n",
            "¿Dudas? Contáctanos:",
            f"{WhatsAppFormatter.CONTACT_URL}",
        ])

        return "\n".join(lines)

    @staticmethod
    def caio_response(is_escalation: bool = False, services: list = None) -> str:
        """Format CAIO agent response for WhatsApp"""
        if services is None:
            services = []

        lines = ["💼 *CONSULTORÍA IA EMPRESARIAL*\n"]

        if is_escalation:
            lines.extend([
                "Detectamos que necesitas implementación personalizada.",
                "Nuestro Chief AI Officer te contactará en 24h.\n",
            ])
        else:
            lines.append("Ofrecemos 4 servicios de consultoría:\n")
            lines.extend([
                "🔍 *AI Audit* - $5k USD (2-3 semanas)",
                "📋 *Strategy & Design* - $10k USD (1 mes)",
                "⚙️ *Implementation* - $25k USD (3-6 meses)",
                "👥 *Team Training* - $5k/mes (ongoing)\n",
            ])

        lines.extend([
            "📞 *AGENDAR CONSULTA:*",
            f"{WhatsAppFormatter.CONTACT_URL}?service=consulting\n",
            "Responde este chat para saber más →",
        ])

        return "\n".join(lines)

    @staticmethod
    def damabook_response(
        ley_21719_relevant: bool = False,
        compliance_areas: list = None,
        escalation_to_legal: bool = False,
    ) -> str:
        """Format DAMABOOK agent response for WhatsApp (Ley 21.719)"""
        if compliance_areas is None:
            compliance_areas = []

        lines = ["📊 *GOBERNANZA DE DATOS - LEY 21.719*\n"]

        if escalation_to_legal:
            lines.extend([
                "Tu caso requiere revisión legal especializada.",
                "Conectándote con nuestro equipo legal...\n",
                "⚖️ Te contactaremos en 48h 📞",
            ])
            return "\n".join(lines)

        if ley_21719_relevant:
            lines.extend([
                "Chile: Ley 21.719 - Protección de Datos Personales ✓\n",
                "📋 *DERECHOS DEL TITULAR:*",
                "• Acceso a datos",
                "• Rectificación",
                "• Supresión (derecho al olvido)",
                "• Oposición",
                "• Portabilidad\n",
            ])

            if compliance_areas:
                lines.append("⚠️ *ÁREAS DE CUMPLIMIENTO DETECTADAS:*")
                for area in compliance_areas:
                    lines.append(f"• {area}")
                lines.append("")

        lines.extend([
            "🛡️ *SERVICIOS OFRECIDOS:*",
            "✓ Data Governance Audit - $3k USD",
            "✓ Compliance Plan - $5k USD",
            "✓ Data Quality Framework - $4k USD",
            "✓ Ongoing Support - $2k/mes\n",
            "📞 *CONSULTA GRATIS:*",
            f"{WhatsAppFormatter.CONTACT_URL}?service=compliance",
        ])

        return "\n".join(lines)

    @staticmethod
    def support_escalation() -> str:
        """Fallback when need human support"""
        return (
            "💬 *SOPORTE TÉCNICO*\n\n"
            "Necesito ayuda de un especialista.\n"
            "Te conecto con nuestro equipo en 24h.\n\n"
            f"📧 {WhatsAppFormatter.CONTACT_URL}"
        )
