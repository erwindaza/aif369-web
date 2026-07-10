"""
Phase 2 Agents: Architecture, ROI, Proposal Generator
"""

import json
from anthropic import Anthropic
from config import MODEL, PlatformState
from knowledge_base import KnowledgeAgent

client = Anthropic()
knowledge_agent = KnowledgeAgent()


class ArchitectureAgent:
    """
    Designs initial architecture recommendations
    based on company profile and scorecard results
    """

    def __init__(self):
        self.system_prompt = """Eres el Architecture Agent de AIF369.

Tu trabajo es diseñar una arquitectura recomendada basado en:
- El contexto del cliente (industria, tamaño, madurez)
- Sus procesos críticos
- Sus dolores principales
- Su presupuesto

Recomienda:
1. Cloud platform (AWS/Azure/GCP)
2. Data layer (databases, data warehouse)
3. AI layer (Claude, fine-tuned models, etc)
4. Orchestration (scheduling, pipelines)
5. Monitoring & Governance
6. Deployment timeline
7. Team requirements
8. Estimated monthly cost

Sé específico. Dame números. Sé realista."""

    async def generate_architecture(self, state: PlatformState) -> dict:
        """Generate architecture recommendation"""

        context = f"""
Cliente: {state.get('name')} en {state.get('company')}
Rol: {state.get('role')}
Industria: {state.get('industry', 'Unknown')}

Contexto:
- Madurez IA actual: {state.get('current_ai_maturity', 0)}/10
- Procesos críticos: {', '.join(state.get('critical_processes', []))}
- Dolores: {', '.join(state.get('main_pains', []))}
- Prioridades: {', '.join(state.get('priorities', []))}
- Presupuesto estimado: {state.get('budget_estimate', 'Unknown')}

Scorecard:
{json.dumps(state.get('scorecard_scores', {}), indent=2)}
"""

        prompt = f"""Basado en este cliente, diseña una arquitectura de IA.

{context}

Formato tu respuesta como:

## ARQUITECTURA RECOMENDADA

### Cloud: [AWS/Azure/GCP]
- Razón: [por qué elegimos esta]

### Data Layer
- [Componentes específicos]

### AI Layer
- [Herramientas, modelos]

### Orquestación
- [Pipelines, scheduling]

### Governance
- [Monitoreo, compliance]

### Timeline
- Fase 1 (semanas 1-4): [qué se hace]
- Fase 2 (semanas 5-8): [qué se hace]
- Fase 3 (semanas 9-12): [qué se hace]

### Team
- [Qué roles se necesitan]

### Estimated Monthly Cost
- Infrastructure: $X,XXX
- Claude API: $X,XXX
- Total: $X,XXX"""

        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=self.system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        architecture = response.content[0].text

        return {
            "agent": "architecture",
            "architecture": architecture,
            "state": state,
        }


class ROIAgent:
    """
    Calculates financial impact of AI implementation
    """

    def __init__(self):
        self.system_prompt = """Eres el ROI Agent de AIF369.

Tu trabajo es calcular el impacto financiero de implementar IA.

Calcula:
1. **Baseline Cost** - Gasto actual en el proceso manual
2. **Cost with AI** - Gasto con IA implementada
3. **Monthly Savings** - Diferencia
4. **Payback Period** - Cuándo se recupera la inversión
5. **3-Year ROI** - Return on investment a 3 años

Usa números reales basado en el contexto del cliente.
Sé conservador (no prometas imposibles).
Desglosa por componente."""

    async def calculate_roi(self, state: PlatformState, architecture: str) -> dict:
        """Calculate financial impact"""

        context = f"""
Cliente: {state.get('name')} en {state.get('company')}
Industria: {state.get('industry', 'Unknown')}
Tamaño: {state.get('company_size', 'Unknown')}

Dolores principales:
{chr(10).join(f"- {pain}" for pain in state.get('main_pains', []))}

Procesos críticos (donde IA puede ayudar):
{chr(10).join(f"- {proc}" for proc in state.get('critical_processes', []))}

Arquitectura recomendada:
{architecture}
"""

        prompt = f"""Calcula el ROI para este cliente:

{context}

Genera un análisis financiero con esta estructura:

## ANÁLISIS FINANCIERO

### Estado Actual (Baseline)
- FTE dedicados a [proceso]: X personas
- Horas/semana: X horas
- Costo mensual: $X,XXX
- Errores/mes: X% → Costo: $X,XXX
- **Total: $X,XXX/mes**

### Con Solución IA
- FTE necesarios: X personas
- Horas/semana: X horas
- Costo mensual: $X,XXX (incluye Claude API)
- Errores/mes: X%
- **Total: $X,XXX/mes**

### Impacto
- **Ahorro mensual: $X,XXX**
- **Ahorro anual: $X,XXX,XXX**

### Inversión
- Implementación: $X,XXX (one-time)
- **Payback: X meses**

### ROI a 3 años
- Total ahorrado: $X,XXX,XXX
- Menos inversión: -$X,XXX
- **Net Benefit: $X,XXX,XXX**
- **ROI: XXX%**

### Beneficios Adicionales (no cuantificados)
- [Mejora de calidad, velocidad, compliance, etc]
"""

        response = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            system=self.system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        roi = response.content[0].text

        return {
            "agent": "roi",
            "roi_analysis": roi,
            "state": state,
        }


class ProposalGenerator:
    """
    Generates executive proposal document
    Combines: scorecard, architecture, ROI
    """

    def __init__(self):
        pass

    async def generate_proposal(
        self,
        state: PlatformState,
        architecture: str,
        roi: str
    ) -> dict:
        """Generate complete proposal"""

        proposal = f"""# PROPUESTA COMERCIAL AIF369

## INFORMACIÓN DEL CLIENTE
- **Empresa**: {state.get('company')}
- **Contacto**: {state.get('name')} ({state.get('role')})
- **Email**: {state.get('email')}
- **Fecha**: {state.get('created_at', 'N/A')}

---

## EXECUTIVE BRIEF

### Situación Actual
{chr(10).join(f"- {pain}" for pain in state.get('main_pains', []))}

Estos desafíos están limitando el crecimiento y creando ineficiencias operacionales.

### Oportunidad
La implementación de IA estratégica puede transformar estos procesos, reduciendo costos
hasta un 40-60% mientras mejora calidad y velocidad.

### Nuestra Recomendación
Implementar una solución de IA integrada sobre los siguientes procesos:
{chr(10).join(f"- {proc}" for proc in state.get('critical_processes', []))}

---

## EVALUACIÓN DE MADUREZ

### AI Scorecard 369
Evaluamos tu madurez actual en 9 dimensiones:

| Dimensión | Score |
|-----------|-------|
{chr(10).join(f"| {dim} | {score}/10 |" for dim, score in state.get('scorecard_scores', {}).items())}

**Resultado General**: {state.get('overall_maturity', 0)}/10

**Interpretación**:
{self._interpret_score(state.get('overall_maturity', 0))}

---

## ARQUITECTURA RECOMENDADA

{architecture}

---

## ANÁLISIS FINANCIERO

{roi}

---

## PLAN DE IMPLEMENTACIÓN

### Fase 1: Descubrimiento (Semanas 1-2)
- Validación de datos y fuentes
- Mapeo detallado de procesos
- Identificación de riesgos y compliance

### Fase 2: Diseño (Semanas 3-4)
- Diseño de modelos y pipelines
- Especificación técnica detallada
- Plan de governance

### Fase 3: Desarrollo (Semanas 5-8)
- Construcción de pipelines
- Training de modelos
- Setup de monitoring

### Fase 4: Piloto (Semanas 9-12)
- Deployment en ambiente controlado
- Validación de resultados
- Ajustes y optimización

### Fase 5: Producción (Semana 13+)
- Rollout gradual
- Monitoreo continuo
- Optimización ongoing

---

## TÉRMINOS Y PRÓXIMOS PASOS

**Inversión**:
- CAIO Advisory: $3,000 USD / 6 meses (diagnóstico + hoja de ruta)
- AI System Creation: $6,000 USD / año (implementación + producción + soporte)

**Próximos Pasos**:
1. Confirmación de interés
2. Workshop de alineación (2 horas)
3. Firma de contrato
4. Inicio de Fase 1

**Validez**: Esta propuesta es válida por 30 días.

---

## SOBRE AIF369

AIF369 es una consultora especializada en transformación con IA para empresas en LATAM.

Nuestro Método 369:
- 3 capas de dirección (Estrategia, Riesgo, Implementación)
- 6 fases de transformación (Descubrir → Escalar)
- 9 métricas de control CAIO

Hemos implementado soluciones de IA en +50 empresas, generando +$200M en valor combinado.

---

**Contacto**:
- Email: edaza@aif369.com
- WhatsApp: +56 9 9754 7192
- Web: aif369.com
"""

        return {
            "agent": "proposal",
            "proposal": proposal,
            "state": state,
        }

    def _interpret_score(self, score: int) -> str:
        if score >= 8:
            return "🚀 **Avanzado**: Ya tienes bases sólidas en IA. Recomendamos escalar y optimizar."
        elif score >= 6:
            return "📈 **Intermedio**: Buen progreso. Necesitas estructura y governance clara."
        elif score >= 4:
            return "🟡 **Básico**: Iniciando en IA. Hay oportunidad grande de crecimiento."
        else:
            return "⚠️ **Inicial**: Estás en el punto de partida. Es el mejor momento para empezar."
