"""
Knowledge Base for Agentic Platform
Contains Método 369, regulations, frameworks, best practices
"""

KNOWLEDGE_BASE = {
    "metodo_369": {
        "name": "Método 369",
        "description": "AIF369 proprietary methodology for AI adoption",
        "content": """
## Método 369

### 3 Capas de Dirección
1. **Capa Estratégica**: Visión, priorización, roadmap de IA
2. **Capa de Riesgo y Cumplimiento**: Risk register, compliance, privacidad
3. **Capa de Implementación**: Arquitectura, MLOps, despliegue en producción

### 6 Fases de Transformación
1. **Descubrir**: Mapear estado actual, oportunidades, capacidades
2. **Diagnosticar**: Evaluar madurez, brechas, riesgos
3. **Diseñar**: Arquitectura, roadmap, gobernanza
4. **Desplegar**: Construcción, testing, lanzamiento
5. **Dominar**: Operación, monitoreo, optimización
6. **Escalar**: Replicar casos de uso, expansión

### 9 Métricas de Control CAIO
1. **Estrategia IA**: Visión clara, alineación ejecutiva, roadmap
2. **Gobierno IA**: Estructura, roles, comités, políticas
3. **Gestión de Riesgos IA**: Identificación, mitigación, monitoreo
4. **Privacidad y Datos**: Calidad, gobernanza, ARCO
5. **AI Factory Design**: Capacidad de build, deploy, scale
6. **Observabilidad de Modelos**: Monitoreo, métricas, alertas
7. **Ética y Responsible AI**: Bias, explicabilidad, fairness
8. **Regulación y Compliance**: Ley 21.719, AI Act, GDPR
9. **Formación y Cultura**: Talento, capacitación, adoption

## Recomendaciones por Sector

### Financiero
- Prioridad: Compliance + Risk
- Focus: Detección de fraude, credit scoring, trading
- Timeline: 6-12 meses

### Retail
- Prioridad: Customer experience + Optimization
- Focus: Demand forecasting, personalization, supply chain
- Timeline: 3-6 meses

### Manufactura
- Prioridad: Operational efficiency
- Focus: Predictive maintenance, quality control, logistics
- Timeline: 6-9 meses

### Salud
- Prioridad: Compliance + Outcomes
- Focus: Diagnostics, patient monitoring, operations
- Timeline: 9-12 meses
"""
    },
    "ley_21719": {
        "name": "Ley 21.719 - Protección de Datos Personales (Chile)",
        "description": "Chilean data protection law effective Dec 1, 2026",
        "content": """
## Ley 21.719: Protección de Datos Personales

### Vigencia
- Entra en vigencia: **1 de diciembre de 2026**
- Quedan menos de 6 meses para cumplimiento

### Conceptos Clave

**Datos Personales**: Información que identifica o puede identificar a una persona

**Responsable de Datos**: Empresa que decide cómo y para qué tratar datos

**Encargado de Datos**: Empresa/proveedor que procesa datos por cuenta del responsable

**Delegado de Protección de Datos (DPD)**: Oficial designado para supervisar cumplimiento

### Derechos ARCO
Toda persona tiene derecho a:

1. **ACCESO**: Solicitar qué datos tenemos
   - Plazo: 15 días hábiles
   - Formato: Digital

2. **RECTIFICACIÓN**: Corregir datos inexactos
   - Plazo: 10 días hábiles

3. **CANCELACIÓN**: Solicitar eliminar datos
   - Excepciones: Auditoría, fraude, legal

4. **OPOSICIÓN**: Rechazar procesamiento para marketing
   - Plazo: 10 días hábiles

### Obligaciones del Responsable
- ✅ Implementar medidas de seguridad (encriptación, acceso restringido)
- ✅ Llevar registro de actividades de tratamiento (RAT)
- ✅ Notificar brechas de datos a DPA dentro de 72 horas
- ✅ Realizar evaluaciones de impacto (EPIA) para datos sensibles
- ✅ Designar Delegado de Protección de Datos
- ✅ Responder solicitudes ARCO en plazo

### Multas
- Leve: 5,000 - 10,000 UTM (incumplimientos menores)
- Grave: 10,000 - 20,000 UTM (incumplimientos severos)
- Muy grave: Hasta 20,000 UTM (brechas sin notificación)

**1 UTM 2026 ≈ $67 USD**
**Multa máxima: ~$1.3M USD**

### Documentos Requeridos
- [ ] Política de Privacidad
- [ ] Registro de Actividades de Tratamiento (RAT)
- [ ] Acuerdos de Procesamiento (DPA) con proveedores
- [ ] Plan de Respuesta ante Brechas
- [ ] Evaluaciones de Impacto (EPIA)
- [ ] Código de Ética (si aplica)
"""
    },
    "ai_act_eu": {
        "name": "EU AI Act",
        "description": "European Union regulation on Artificial Intelligence",
        "content": """
## EU AI Act

### Scope
Applies to AI systems provided or used in EU, regardless of developer location

### Risk Levels & Requirements

**Prohibited (High Risk)**
- Social scoring
- Facial recognition without consent
- Emotional recognition in children
- Subliminal manipulation

**High Risk** (Require governance)
- Critical infrastructure control
- Law enforcement
- Employment/HR decisions
- Education
- Finance/credit
- Border/migration control

**Medium Risk**
- Chatbots (must disclose AI use)
- Content recommendation
- Emotion detection

**Low Risk**
- Video games
- Spam filters
- Backup systems

### Technical Requirements (High Risk)
- ✅ Risk assessments
- ✅ Quality management system
- ✅ Data governance
- ✅ Logging and monitoring
- ✅ Cybersecurity measures
- ✅ Human oversight
- ✅ Transparency/documentation
- ✅ Model card requirements

### Timeline
- April 2024: Prohibited systems banned
- June 2024: Governance requirements begin
- January 2025: Full implementation
- Chile: Not directly applicable, but serves as reference
"""
    },
    "frameworks": {
        "name": "AI Governance Frameworks",
        "description": "NIST, ISO, DAMA standards",
        "content": """
## AI Governance Frameworks

### NIST AI Risk Management Framework
**6 Core Functions:**
1. Govern - Strategy, policies, oversight
2. Map - Understand AI system, risks, impacts
3. Measure - Assess performance, risks
4. Manage - Implement controls
5. Report - Communicate findings
6. Monitor - Ongoing evaluation

**Use case for AIF369**: Helps structure governance decisions

### ISO 42001: AI Management System
**Requirements:**
- Leadership commitment
- Risk management
- Data management
- Model management
- Human oversight
- Monitoring & control
- Incident management

**Certification path**: 9-12 months

### ISO 23894: AI Governance
**Scope**: Governance processes for AI systems
**Focus:**
- Stakeholder engagement
- Accountability
- Transparency
- Risk management
- Value creation

### DAMA Data Management
**9 Knowledge Areas:**
1. Data Governance
2. Data Architecture
3. Data Modeling
4. Data Storage & Operations
5. Data Security
6. Data Quality
7. Master & Reference Data
8. Data Warehousing & Analytics
9. Document & Content Management

**For AI**: Critical for data foundations
"""
    },
    "case_studies": {
        "name": "Case Studies",
        "description": "Real AIF369 implementations",
        "content": """
## AIF369 Case Studies

### Case 1: Financial Services Company (Chile)
**Challenge**: Manual credit scoring, 40% error rate
**Solution**: AI model + governance framework
**Results**:
- Error rate: 40% → 3%
- Processing time: 3 days → 2 hours
- Cost savings: $180k/month
- ROI: 6 months

### Case 2: Retail Chain (LATAM)
**Challenge**: Inventory forecasting, $5M annual waste
**Solution**: Demand forecasting AI + supply chain optimization
**Results**:
- Waste: $5M → $1.2M annually
- Stock-out incidents: -65%
- Carrying costs: -40%
- Revenue impact: +$3.2M

### Case 3: Manufacturing (Colombia)
**Challenge**: Preventive maintenance, 15% equipment downtime
**Solution**: Predictive maintenance model
**Results**:
- Downtime: 15% → 3%
- Maintenance costs: -$400k/year
- Production increase: +18%
- Safety incidents: -60%

## Success Factors
1. **Executive alignment** - CEO/board buy-in
2. **Data quality** - Clean, labeled data
3. **Governance first** - Before AI implementation
4. **Iterative approach** - Start with pilot
5. **Team capability** - Right skills on board
"""
    }
}


def get_knowledge(query: str) -> str:
    """
    Simple retrieval from knowledge base.
    In production, use vector embeddings for semantic search.
    """
    query_lower = query.lower()

    # Simple keyword matching (will upgrade to semantic search in Phase 3)
    keywords_map = {
        "metodo": "metodo_369",
        "método": "metodo_369",
        "369": "metodo_369",
        "ley 21": "ley_21719",
        "21.719": "ley_21719",
        "arco": "ley_21719",
        "datos personales": "ley_21719",
        "privacidad": "ley_21719",
        "compliance": "ley_21719",
        "eu ai act": "ai_act_eu",
        "ai act": "ai_act_eu",
        "nist": "frameworks",
        "iso": "frameworks",
        "dama": "frameworks",
        "governance": "frameworks",
        "case": "case_studies",
        "ejemplo": "case_studies",
    }

    # Find matching knowledge base section
    for keyword, section in keywords_map.items():
        if keyword in query_lower:
            return KNOWLEDGE_BASE.get(section, {}).get("content", "No encontrado")

    # Default: return all available knowledge
    return "Disponible: Método 369, Ley 21.719, AI Act, Frameworks, Case Studies. ¿Cuál te interesa?"


class KnowledgeAgent:
    """Query AI knowledge base for governance/methodology guidance"""

    def __init__(self):
        self.knowledge = KNOWLEDGE_BASE

    async def answer_question(self, user_query: str, context: str = "") -> str:
        """Answer user question using knowledge base + Claude reasoning"""
        from anthropic import Anthropic
        from config import MODEL

        client = Anthropic()

        # Get relevant knowledge
        knowledge = get_knowledge(user_query)

        # Use Claude to reason over knowledge + context
        prompt = f"""Eres el Knowledge Agent de AIF369. Tienes acceso a nuestra base de conocimiento.

Usuario pregunta: "{user_query}"

Contexto del cliente:
{context}

Conocimiento relevante:
{knowledge}

Proporciona una respuesta clara, basada en los datos disponibles.
Si hay regulaciones relevantes, mencionalas.
Si hay un caso de uso similar, cuéntalo.
Máximo 3-4 párrafos."""

        response = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        return response.content[0].text
