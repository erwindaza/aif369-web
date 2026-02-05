# Arquitectura AIF369 - Roadmap

## Fase 1: Formulario de Contacto (Actual) ✅
```
Sitio Web (Vercel) → Cloud Run API → BigQuery
```

## Fase 2: Agentes Conversacionales (Próximo)

### Arquitectura propuesta:
```
Usuario (Web/Chat) 
    ↓
Cloud Run (API Gateway)
    ↓
    ├─→ Agent Orchestrator (Python/LangChain)
    │       ↓
    │       ├─→ LLM (Vertex AI / OpenAI)
    │       ├─→ Vector DB (Pinecone/Chroma) - Conocimiento
    │       └─→ BigQuery - Contexto histórico
    ↓
BigQuery - Logs de conversaciones
```

### Componentes clave para agentes:

**1. API Gateway (Cloud Run)** 
- Endpoint: `/api/chat`
- Autoscaling: 0-100 instancias
- Maneja WebSockets para chat en tiempo real

**2. Agent Orchestrator**
- Framework: LangChain o LlamaIndex
- Gestiona contexto de conversación
- Accede a base de conocimiento vectorial
- Consulta BigQuery para datos históricos

**3. Almacenamiento**
- **BigQuery**: Logs de todas las conversaciones
- **Vector DB**: Documentación, FAQs, casos de uso
- **Firestore**: Sesiones activas de chat

**4. Escalabilidad**
- Cloud Run autoscala según requests
- Sin estado (stateless) - sesiones en Firestore
- Load balancer automático
- Cold start < 1 segundo

### Estimación de costos (1000 usuarios concurrentes):

| Recurso | Configuración | Costo/mes |
|---------|---------------|-----------|
| Cloud Run | 2 vCPU, 4GB RAM | ~$50 |
| Vertex AI (LLM) | 1M tokens | ~$50-200 |
| BigQuery | 100GB storage | ~$5 |
| Firestore | 1GB, 1M reads | ~$10 |
| **Total estimado** | | **~$115-265/mes** |

### Tecnologías recomendadas:

```python
# requirements.txt para agentes
langchain==0.1.0
openai==1.10.0
google-cloud-aiplatform==1.40.0  # Vertex AI
pinecone-client==3.0.0
chromadb==0.4.22
tiktoken==0.5.2
```

### Estructura de código sugerida:

```
backend/
├── main.py              # API Gateway
├── agents/
│   ├── orchestrator.py  # Gestión de agentes
│   ├── tools.py         # Herramientas (BigQuery, APIs)
│   └── prompts.py       # Prompts para LLM
├── vectordb/
│   ├── embeddings.py    # Generación de embeddings
│   └── retrieval.py     # Búsqueda semántica
└── chat/
    ├── session.py       # Gestión de sesiones
    └── websocket.py     # WebSocket handler
```

### Implementación por fases:

**Sprint 1 (2-3 semanas):**
- ✅ Formulario de contacto funcionando
- Setup básico de LangChain
- Primer agente simple (Q&A)

**Sprint 2 (2-3 semanas):**
- Vector DB con documentación
- Agente con contexto mejorado
- UI de chat en el sitio web

**Sprint 3 (2-3 semanas):**
- Múltiples agentes especializados
- Handoff a humano cuando sea necesario
- Analytics de conversaciones

**Sprint 4 (2-3 semanas):**
- Optimizaciones de performance
- A/B testing de prompts
- Monitoring y alertas

---

**Ventajas de esta arquitectura:**

✅ **Escalable**: Cloud Run maneja picos de tráfico automáticamente  
✅ **Cost-effective**: Pagas solo por uso (scale to zero)  
✅ **Flexible**: Fácil cambiar LLMs o agregar herramientas  
✅ **Observable**: Todos los logs en BigQuery para análisis  
✅ **Multi-agente**: Puedes tener agentes especializados por tema  

---

**¿Necesitas que prepare algún componente específico mientras se instala Docker?**
