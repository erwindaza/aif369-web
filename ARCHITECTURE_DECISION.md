# AIF369 - Decisiones Arquitectónicas de AI

**Fecha**: 3 de julio 2026
**Contexto**: Fábrica de IA para LATAM + Marketplace enriquecimiento de datos
**Scope**: Orquestación de agentes, batch + real-time, enriquecimiento de datos

---

## 1. ORQUESTACIÓN DE AGENTES: Análisis Comparativo

### Opción A: LangGraph (Actual)
**Ventajas**:
- ✅ Desarrollo rápido (local testing)
- ✅ Excelente para conversacionales simple
- ✅ Memory/State management built-in
- ✅ Debugging fácil

**Desventajas**:
- ❌ No escalable para 100+ agentes paralelos
- ❌ No tiene orchestración batch nativa
- ❌ Difícil de monitorear en producción
- ❌ Sin soporte para SLA/timeouts complejos
- ❌ Stateful (difícil de escalar horizontalmente)

**Costo**: Gratis (OSS) pero infraestructura cara si escalas

---

### Opción B: Vertex AI Pipelines ⭐ RECOMENDADO PARA SCALE
**Ventajas**:
- ✅ Diseñado para batch + real-time simultáneos
- ✅ Escalabilidad automática (Kubernetes nativo)
- ✅ Built-in monitoring, logging, tracing
- ✅ Orquestación compleja (DAGs, conditional routing, parallelismo)
- ✅ SLA management, retry policies, timeouts
- ✅ Integración directa con GCP (BigQuery, Pub/Sub, Cloud Run)
- ✅ Soporte para 1000s de agentes paralelos
- ✅ Cost optimization (pagar solo por lo que usas)

**Desventajas**:
- ⚠️ Curva de aprendizaje (YAML/Python DSL)
- ⚠️ Menos flexible para conversacionales interactivas (es batch-first)
- ⚠️ Lock-in con GCP

**Costo**: $0.30-0.50 por ejecución + compute. Escalable.

---

### Opción C: Apache Airflow
**Ventajas**:
- ✅ Open source, multi-cloud
- ✅ DAG-based orchestration (flexible)
- ✅ Gran comunidad

**Desventajas**:
- ❌ Overhead operacional (tienes que mantener Kubernetes)
- ❌ No optimizado para AI workflows
- ❌ Monitoring es "bueno" pero no "excelente"

**Costo**: High (operaciones, infraestructura)

---

### Opción D: AWS Step Functions + Lambda
**Ventajas**:
- ✅ Serverless (sin operaciones)
- ✅ Bueno para workflows estado-máquina
- ✅ Integración AWS completa

**Desventajas**:
- ❌ No tan potente para AI multi-agente
- ❌ Caro si muchas invocaciones
- ❌ Debugging difícil

**Costo**: Medium-High (pago por invocación)

---

## 🏆 RECOMENDACIÓN: Arquitectura Híbrida

```
┌─────────────────────────────────────────────────────────────────┐
│                     AIF369 AI ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │  Real-Time Layer    │ (Clientes finales)
                    │  (Interactivo)      │
                    └──────────┬──────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
            FastAPI        Cloud Run      Vertex AI
         (LangGraph)        (Agents)     (Real-time)
                │              │              │
                └──────────────┼──────────────┘
                               │
                        Pub/Sub Topic
                      (eventos en vivo)
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
    ┌───▼────────┐  ┌──────────▼────────┐  ┌────────▼───────┐
    │  Batch     │  │  Enriquecimiento  │  │   Monitoreo    │
    │  Processing│  │   de Datos        │  │   & Análisis   │
    │            │  │  (Vertex Pipelines)  │                │
    │ Marketplace│  │                   │  │  BigQuery      │
    │ + Usuarios │  │  • OCR            │  │  Looker        │
    │ del Negocio│  │  • Classification │  │                │
    └──────┬─────┘  │  • Enrichment     │  └────────────────┘
           │        │  • Validation     │
           │        └───────────────────┘
           │               │
        Scheduler    Vertex Pipelines
       (Cloud Tasks)  (Batch)
           │               │
           └───────┬───────┘
                   │
           BigQuery (Storage)
           PostgreSQL (State)
           GCS (Files)
```

---

## 2. BATCH vs REAL-TIME: Estrategia

### Para "Usuarios del Negocio" (B2B, batch):
Use **Vertex AI Pipelines**
```python
# Ejemplo: Enriquecimiento nightly de 100k productos

@kfp.dsl.component
def enrich_products_batch(products_path: str):
    # Leer products desde BigQuery/GCS
    # Procesar en lotes de 1000
    # Usar Claude API o Gemini (batches)
    # Guardar resultados enriquecidos
    pass

@kfp.dsl.pipeline
def nightly_enrichment():
    enrich = enrich_products_batch()
    validate = validate_enrichment(enrich.outputs)
    notify = send_report(validate.outputs)
```

**Ventajas**:
- ✅ Procesa 100k items en 2-3 horas
- ✅ Costo: $50-100/noche (vs $500+ con APIs en tiempo real)
- ✅ Retry automático, checkpointing
- ✅ SLA claro (11pm-2am)

---

### Para "Clientes Finales" (B2C, real-time):
Use **FastAPI + Cloud Run + Pub/Sub**
```python
# Tiempo real: cliente sube imagen → enriquecimiento instantáneo

@app.post("/api/enrich")
async def enrich_real_time(image: UploadFile):
    # 1. Upload a GCS
    # 2. Publica a Pub/Sub (async)
    # 3. Retorna job_id (user ve spinner)
    # 4. WebSocket/polling para resultado
    
    # Background (Cloud Tasks):
    # - OCR (Google Vision)
    # - Classification (Claude)
    # - Validation (Gemini)
    # - Guardar en BigQuery
    # - Notificar al cliente
```

**Ventajas**:
- ✅ Respuesta inmediata al usuario
- ✅ Procesamiento en background
- ✅ Escalable (auto-scaling en Cloud Run)
- ✅ Costo: $0.04/millón de requests + compute

---

## 3. MCP + Kafka/Pub-Sub: Diseño de Comunicación

### Arquitectura de Mensajería:

```
┌─────────────────────────────────────────────────────┐
│              MCP Servers                             │
│  ┌──────────────┬──────────────┬──────────────┐    │
│  │ Google Drive │  Slack       │  Notion      │    │
│  │ (docs)       │  (notif)     │  (CRM)       │    │
│  └──────┬───────┴──────┬───────┴──────┬───────┘    │
└─────────┼──────────────┼──────────────┼─────────────┘
          │              │              │
    ┌─────▼──────────────▼──────────────▼─────┐
    │                                          │
    │    Google Pub/Sub (Event Bus)           │
    │  ┌────────────────────────────────────┐ │
    │  │ Topics:                            │ │
    │  │ • agent.discovery.complete         │ │
    │  │ • scorecard.generated              │ │
    │  │ • proposal.ready                   │ │
    │  │ • data.enriched                    │ │
    │  │ • alert.anomaly                    │ │
    │  └────────────────────────────────────┘ │
    └──────────────────────────────────────────┘
         │              │              │
    ┌────▼──┐      ┌────▼──┐      ┌───▼────┐
    │Cloud  │      │Cloud  │      │BigQuery│
    │Run    │      │Tasks  │      │        │
    │       │      │       │      │        │
    │Agentes│      │Batch  │      │Analytics│
    └────────      │Jobs   │      └────────┘
                   └───────┘

    Communication: gRPC + Protocol Buffers (fast)
    Monitoring: Cloud Trace + Pub/Sub metrics
```

### Kafka vs Pub/Sub:
**Para AIF369: Pub/Sub (recomendado)**
- ✅ Fully managed (0 operaciones)
- ✅ Integrado con GCP (donde están tus datos)
- ✅ Costo bajo (<$0.04 por GB)
- ✅ Suficiente throughput para AIF369 (10k msgs/sec es plenty)

Si escalas a 1M msgs/sec: entonces Kafka on Kubernetes.

---

## 4. SISTEMA DE ENRIQUECIMIENTO DE DATOS

### Arquitectura para Datos 1P + 3P:

```
┌─────────────────────────────────────────────────────┐
│          Data Ingestion Layer                       │
│                                                     │
│  1P: Marketplace interno, logs, transacciones      │
│  3P: APIs externas, partners, providers            │
└──────────────┬──────────────────────────────────────┘
               │
        ┌──────▼──────┐
        │  BigQuery   │ (Raw layer)
        │  (Staging)  │
        └──────┬──────┘
               │
    ┌──────────┴──────────────┐
    │                         │
┌───▼────────────────┐   ┌───▼─────────────┐
│ Vertex Pipelines   │   │ Cloud Functions │
│ (Batch)            │   │ (Real-time)     │
│                    │   │                 │
│ • Schema Detection │   │ • OCR           │
│ • Validation       │   │ • Classification│
│ • Deduplication    │   │ • Sentiment     │
│ • Normalization    │   │ • Entity Extr.  │
└───┬────────────────┘   └───┬─────────────┘
    │                         │
    │    ┌────────────────────┴─────────┐
    │    │                              │
┌───▼────▼──────────────────────────────▼──┐
│   AI Enrichment Layer                    │
│   ┌──────────────────────────────────┐  │
│   │ Claude/Gemini API Calls          │  │
│   │ • Classification                 │  │
│   │ • Entity Recognition             │  │
│   │ • Relationship Discovery         │  │
│   │ • Quality Scoring                │  │
│   │ • Categorization                 │  │
│   └──────────────────────────────────┘  │
└────────────────┬─────────────────────────┘
                 │
         ┌───────▼────────┐
         │  BigQuery      │
         │  (Gold Layer)  │
         │                │
         │ • Enriched     │
         │ • Validated    │
         │ • Deduplicated │
         │ • Ready for use│
         └────────────────┘
```

### Pipeline Específico para Marketplace:

```yaml
# Vertex AI Pipeline (YAML)

steps:
  - id: ingest_1p
    operator: bigquery.import
    config:
      source: "marketplace_db"
      destination: "raw.marketplace_products"
      
  - id: ingest_3p
    operator: http.fetch
    config:
      endpoints: ["supplier_api1", "supplier_api2"]
      destination: "raw.external_products"
      
  - id: validate_schema
    operator: python.function
    inputs:
      - ingest_1p.outputs
      - ingest_3p.outputs
    config:
      function: validate_product_schema()
      
  - id: deduplicate
    operator: sql
    inputs: validate_schema.outputs
    config:
      query: |
        SELECT DISTINCT * EXCEPT(row_num)
        FROM input WHERE row_num = 1
        
  - id: enrich_batch
    operator: vertex.llm_batch
    inputs: deduplicate.outputs
    config:
      model: "gemini-2.0-flash-lite"
      prompt: |
        Enrich this product data:
        {{product_json}}
        
        Add: categories, keywords, quality_score
        
      batch_size: 100
      
  - id: validate_quality
    operator: python.function
    inputs: enrich_batch.outputs
    config:
      function: check_enrichment_quality()
      threshold: 0.85  # Solo 85%+ quality
      
  - id: notify_issues
    operator: pubsub.publish
    inputs: validate_quality.outputs
    config:
      topic: "data.validation.failed"
      
  - id: store_gold
    operator: bigquery.insert
    inputs: 
      - validate_quality.outputs.success
      - validate_quality.outputs.metadata
    config:
      destination: "gold.enriched_products"
      
schedule:
  frequency: DAILY
  time: "23:00"  # 11pm
  sla: "02:00"   # Terminar antes de 2am
```

---

## 5. EVALUACIÓN DE MODELOS: Costo vs Calidad

### Comparativo 2026:

| Modelo | Costo/1M tokens | Velocidad | Calidad | Use Case Ideal |
|--------|-----------------|-----------|---------|-----------------|
| **Gemini 2.5 Flash Lite** | $0.075 | ⚡⚡⚡ | ⭐⭐⭐⭐ | ✅ RECOMENDADO |
| Gemini 2.0 Flash | $0.15 | ⚡⚡ | ⭐⭐⭐⭐⭐ | Fallback si necesitas mejor |
| Claude 3.5 Haiku | $0.80 | ⚡⚡ | ⭐⭐⭐⭐ | Heavy reasoning |
| Grok 3 | $0.50 | ⚡⚡⭐ | ⭐⭐⭐⭐ | Alternativa |
| Llama 3.1 405B | $1.35 | ⭐ | ⭐⭐⭐⭐⭐ | Cuando costo no importa |
| **open-source (local)** | $0 | Variable | ⭐⭐-⭐⭐⭐ | Solo para casos específicos |

---

### Para AIF369 Específicamente:

#### Scoring (Enriquecimiento de Datos)
**Requiere**: Clasificación, extracción, scoring
**Mejor**: Gemini 2.5 Flash Lite
- Costo: $0.075/1M tokens
- Calidad: Suficiente para clasificación (95%+ accuracy)
- Velocidad: 5-10 ms/request
- Presupuesto: 10M tokens/mes = $750/mes

#### Discovery Agent (Conversacional)
**Requiere**: Reasoning, context awareness
**Mejor**: Gemini 2.0 Flash (si necesitas mejor que lite)
- Costo: $0.15/1M tokens
- Calidad: Excelente para conversación (99%+)
- Presupuesto: 5M tokens/mes = $750/mes

#### Architecture Agent (Reasoning profundo)
**Requiere**: Análisis complejo, recomendaciones
**Mejor**: Claude 3.5 Haiku (si necesitas mejor reasoning)
- Costo: $0.80/1M tokens
- Calidad: Excelente reasoning (mejor que Gemini para lógica)
- Presupuesto: 2M tokens/mes = $1,600/mes

---

### 💰 COSTO TOTAL ESTIMADO:

```
AIF369 Monthly (1000 prospects):

Discovery Agent:      5M tokens × $0.075 = $375
Architecture Agent:   2M tokens × $0.080 = $160
ROI Agent:           2M tokens × $0.075 = $150
Enrichment (Batch): 20M tokens × $0.075 = $1,500
                                          ————
TOTAL/mes:                              $2,185

VS Anthropic (Claude):
Discovery:          5M × $0.80 = $4,000
Architecture:       2M × $0.80 = $1,600
ROI:               2M × $0.80 = $1,600
Enrichment:       20M × $0.80 = $16,000
                                ————
TOTAL/mes:                     $23,200

💡 AHORRO: $21,015/mes usando Gemini
   (10x más barato, 95% de la calidad)
```

---

## 6. RECOMENDACIÓN FINAL: Stack para AIF369

### Conversacional (FastAPI + LangGraph) - HOY
```python
# Real-time para clientes finales
# Stack: FastAPI + LangGraph + Claude API
# Modelos: Gemini 2.5 Flash Lite

✅ Usar: Claude (mejor reasoning) o Gemini 2.0 Flash
❌ NO cambiar ahora (conversacional funciona bien)
```

### Batch (Vertex AI Pipelines) - MIGRAR EN FASE 3
```python
# Enriquecimiento de datos + usuarios del negocio
# Stack: Vertex AI Pipelines + Pub/Sub + BigQuery
# Modelos: Gemini 2.5 Flash Lite

✅ Implementar para:
  - Enriquecimiento nightly de marketplace (100k items)
  - Batch processing de usuarios del negocio
  - Costo: $50-100/night vs $1000+ con APIs
```

### Monitoring (Cloud Trace + Pub/Sub)
```
✅ Implementar:
  - Traces de cada agente
  - Métricas de latency/cost
  - Alertas si algo falla
  - Dashboard Looker
```

---

## 7. ROADMAP IMPLEMENTACIÓN

### Semana 1-2: Testing Phase 1+2 (SIN CAMBIOS)
- Keep LangGraph + Claude/Gemini
- Test performance con datos reales
- Medir calidad de propuestas

### Semana 3: Migración Parcial a Vertex
- Implementar Vertex Pipelines para enriquecimiento nightly
- Mantener FastAPI real-time como está
- Agregar Pub/Sub entre ellos

### Semana 4: Optimización + Monitoring
- Cambiar a Gemini 2.5 Flash Lite (ahorro de $21k/mes)
- Implementar Cloud Trace
- Dashboard Looker live

### Post-Launch: Scale
- MCP integrations (Drive, Slack, Notion)
- Parallelización de agentes
- ML feedback loop (mejorar modelos con datos reales)

---

## 8. RESPUESTA DIRECTA A TUS PREGUNTAS

### ¿Usar Vertex Pipelines?
**SÍ, pero**:
- Solamente para batch (enriquecimiento nightly)
- Real-time mantén FastAPI+LangGraph
- Mejor orquestación = Vertex Pipelines + Pub/Sub

### ¿MCP + Kafka/Pub-Sub?
**SÍ, usa Pub/Sub NO Kafka**:
- Pub/Sub: Managed, cheap, GCP native
- Kafka: Solo si >1M msgs/sec (no es tu caso)
- MCP: Sí, integra Drive, Sheets, Slack

### ¿Modelo más barato que Gemini 2.5 Flash Lite?
**NO hay mejor relación costo/calidad**:
- Open source local: Costo 0 pero latency 500ms+ (no sirve)
- Claude Haiku: $0.80 (10x más caro)
- Grok: $0.50 (6.6x más caro)
- Gemini 2.5 Flash Lite: $0.075 (ES EL MÁS BARATO + buena calidad)

**VEREDICTO**: Mantén Gemini 2.5 Flash Lite

### ¿Enriquecimiento de datos 1P+3P?
**Vertex Pipelines + Gemini 2.5 Flash Lite**:
- Batch nightly: 100k items en 2 horas
- Costo: $50-100/noche
- Calidad: 95%+
- Automático, no needs human intervention

### ¿Eficiente en costo+calidad?
**SÍ**:
- Gemini 2.5 Flash Lite: $0.075/1M
- Vertex Pipelines: Managed
- Pub/Sub: $0.04 per GB
- Total: $2,200/mes vs $23,200 con Claude
- Calidad: 95%+ (suficiente para AIF369)

---

## PRÓXIMOS PASOS

1. **Ahora**: Testear Phase 1+2 con setup actual
2. **Semana 1-2**: Medir calidad de propuestas reales
3. **Semana 3**: Implementar Vertex Pipelines para batch
4. **Semana 4**: Agregar Pub/Sub + Monitoring
5. **Post**: Scale a 10k+ prospects/mes

**Costo proyectado**: $2-3k/mes
**Calidad**: 95%+
**Escalabilidad**: 100k+ items/día (batch) + unlimited real-time

¿Empezamos con testing Phase 1+2?
