# AIF369 Agentic Data Platform — Plan Ejecutivo

**Status**: Iniciando Phase 0 (Repository Setup)
**Timeline**: 4 fases + producción
**Stack**: dbt + RAG + MCP + LangGraph + Cloud Portable
**Cost**: $0 local, $5-10/mes AWS+GCP

---

## ARQUITECTURA INTEGRAL

```
┌─────────────────────────────────────────────────────────┐
│                    User Interaction                      │
│  (Chat conversacional sobre perfiles + datos)           │
└──────────────────────┬──────────────────────────────────┘
                       │
            ┌──────────▼──────────┐
            │  LangGraph Agents   │  ← Conversacional
            │  (Profile, Recom)   │    (MANTENEMOS)
            └──────────┬──────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
   ┌───▼───┐      ┌───▼───┐      ┌───▼────┐
   │  RAG  │      │  MCP  │      │ Metrics│
   │(Chroma)      │ Tools │      │ (dbt)  │
   └───┬───┘      └───┬───┘      └───┬────┘
       │               │               │
       └───────────────┼───────────────┘
                       │
            ┌──────────▼──────────┐
            │  FastAPI Backend    │
            │  (orchestration)    │
            └──────────┬──────────┘
                       │
       ┌───────────────┴───────────────┐
       │                               │
   ┌───▼──────────┐        ┌──────────▼────┐
   │ Profile 360  │        │  Vector Store │
   │ (dbt output) │        │  (embeddings) │
   └───┬──────────┘        └──────────┬────┘
       │                              │
   ┌───▼──────────────────────────────▼───┐
   │     Data Layer (DuckDB / Postgres)    │
   │  Raw → Staging → Intermediate → Mart  │
   └───────────────────────────────────────┘
        │              │                 │
    ┌───▼───┐      ┌───▼───┐        ┌───▼────┐
    │ Local │      │  AWS  │        │  GCP   │
    │DuckDB │      │  S3   │        │BigQuery│
    │ (now) │      │(demo) │        │(future)│
    └───────┘      └───────┘        └────────┘
```

---

## PHASE 0: Repository Setup (AHORA)

### Crear estructura base:

```bash
mkdir -p aif369-agentic-data-platform
cd aif369-agentic-data-platform

# Crear folders
mkdir -p dbt api agents rag mcp infra/aws infra/gcp docs data/{raw,processed}

# Crear archivos base
touch README.md .env.example docker-compose.yml
touch dbt/dbt_project.yml
touch api/main.py
touch agents/graph.py
touch rag/embeddings.py
touch mcp/server.py
```

### Estructura esperada:
```
aif369-agentic-data-platform/
├── dbt/
│   ├── models/
│   │   ├── staging/stg_profiles.sql
│   │   ├── intermediate/int_profile_enrichment.sql
│   │   └── marts/profile_360.sql
│   └── dbt_project.yml
│
├── api/
│   ├── main.py (FastAPI)
│   └── requirements.txt
│
├── agents/
│   ├── graph.py (LangGraph conversacional)
│   └── tools.py
│
├── rag/
│   ├── embeddings.py (local embeddings)
│   ├── retriever.py
│   └── vector_store.py (ChromaDB)
│
├── mcp/
│   ├── server.py (MCP server)
│   └── tools.py (get_profile, search_profiles, etc)
│
├── infra/
│   ├── aws/
│   │   ├── lambda_handler.py
│   │   └── deployment.yaml
│   └── gcp/
│       ├── cloud_run_deployment.yaml
│       └── main.py
│
├── docs/
│   ├── architecture.md
│   ├── phase_roadmap.md
│   └── deployment_guides.md
│
├── data/
│   ├── raw/
│   │   └── sample_profiles.csv
│   └── processed/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## PHASE 1: Local PoC - Profile 360

### Objetivo:
```
CSV → dbt (staging/intermediate/marts) → profile_360 table → RAG index → MCP tools → LangGraph
```

### Entregables:

#### 1. dbt Models (transformación)
```sql
-- dbt/models/staging/stg_profiles.sql
{{ config(materialized='table') }}

SELECT
    CAST(profile_id AS STRING) as profile_id,
    full_name,
    email,
    company,
    role,
    country,
    skills,
    interests,
    created_at,
    updated_at
FROM {{ source('raw', 'profiles') }}
WHERE is_active = true

-- dbt/models/marts/profile_360.sql
{{ config(materialized='table') }}

WITH enriched AS (
    SELECT
        p.profile_id,
        p.full_name,
        p.email,
        p.company,
        p.role,
        p.country,
        p.skills,
        p.interests,
        COUNT(i.interaction_id) as total_interactions,
        MAX(i.interaction_date) as last_interaction_date,
        ROUND(COUNT(i.interaction_id) * 10 / 100, 2) as profile_score,
        'AI Summary placeholder' as ai_summary,
        'Recommended: Schedule intro call' as recommended_next_action,
        MD5(p.profile_id) as embedding_id
    FROM {{ ref('stg_profiles') }} p
    LEFT JOIN {{ ref('stg_interactions') }} i USING (profile_id)
    GROUP BY 1,2,3,4,5,6,7,8
)
SELECT * FROM enriched
```

#### 2. FastAPI Backend
```python
# api/main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import duckdb

app = FastAPI()
conn = duckdb.connect('data/profiles.duckdb')

@app.get("/api/profiles/{profile_id}")
async def get_profile(profile_id: str):
    result = conn.execute(
        "SELECT * FROM profile_360 WHERE profile_id = ?",[profile_id]
    ).fetchall()
    return {"profile": result}

@app.post("/api/chat")
async def chat(message: str, session_id: str):
    # LangGraph agent processes message
    # Uses RAG + MCP tools
    # Returns response
    pass
```

#### 3. LangGraph Agents (conversacional sobre datos)
```python
# agents/graph.py
from langgraph.graph import StateGraph

def profile_agent(state):
    """Agente que responde sobre perfiles usando Profile 360"""
    # Query Profile 360 based on user question
    # Use MCP tools for metrics
    # Generate response
    return state

def recommendation_agent(state):
    """Agente que recomienda acciones"""
    # Analyze profile score + interactions
    # Generate next action recommendation
    return state
```

#### 4. RAG + Embeddings
```python
# rag/embeddings.py
from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer('all-MiniLM-L6-v2')  # Local, gratis
chroma_client = chromadb.Client()

# Index Profile 360 documents
for profile in profiles:
    embedding = model.encode(profile['ai_summary'])
    chroma_client.add(
        ids=[profile['profile_id']],
        embeddings=[embedding],
        documents=[profile['ai_summary']]
    )
```

#### 5. MCP Tools (query safe metrics)
```python
# mcp/tools.py
def get_profile(profile_id: str) -> dict:
    """Fetch profile from Profile 360"""
    return conn.execute(
        "SELECT * FROM profile_360 WHERE profile_id = ?",
        [profile_id]
    ).fetchall()

def search_profiles(query: str) -> list:
    """Semantic search usando RAG"""
    results = chroma_client.query(query)
    return results

def get_recommended_action(profile_id: str) -> str:
    """Get recommended next action from Profile 360"""
    profile = get_profile(profile_id)
    return profile['recommended_next_action']

def run_safe_metric_query(metric: str) -> float:
    """Run pre-approved metrics from dbt models"""
    approved_metrics = {
        'avg_profile_score': "SELECT AVG(profile_score) FROM profile_360",
        'total_profiles': "SELECT COUNT(*) FROM profile_360",
        'engagement_rate': "SELECT AVG(total_interactions) FROM profile_360"
    }
    if metric in approved_metrics:
        return conn.execute(approved_metrics[metric]).fetchone()[0]
```

---

## PHASE 2: AWS Demo - El Androide

### Objetivo:
Portfolio técnico demostrable en AWS

### Stack:
- S3 (data storage)
- Lambda (serverless API)
- Bedrock (Claude/Llama para agentic responses)
- CloudWatch (logging)

### Entregable:
```python
# infra/aws/lambda_handler.py
import json
import boto3
from agents.graph import profile_agent

bedrock = boto3.client('bedrock-runtime')

def lambda_handler(event, context):
    body = json.loads(event['body'])
    profile_id = body['profile_id']
    message = body['message']
    
    # Use profile agent with Bedrock
    response = profile_agent({
        'profile_id': profile_id,
        'message': message,
        'llm': bedrock  # Use Bedrock instead of local LLM
    })
    
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
```

---

## PHASE 3: GCP Integration - AIF369.com

### Objetivo:
AIF369.com consume Agentic Data API

### Stack:
- Cloud Run (API)
- Secret Manager (credentials)
- Cloud Logging (observability)

### Entregable:
```yaml
# infra/gcp/cloud_run_deployment.yaml
apiVersion: v1
kind: Service
metadata:
  name: aif369-agentic-api

spec:
  template:
    spec:
      containers:
      - image: gcr.io/aif369-backend/agentic-api:latest
        env:
        - name: LLM_PROVIDER
          valueFrom:
            secretKeyRef:
              name: aif369-secrets
              key: llm_provider
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: aif369-secrets
              key: database_url
```

---

## PHASE 4: Cloud Portability - Adapters

### Objetivo:
Poder cambiar cloud sin reescribir código

### Adapters necesarios:

**Data Layer**:
- DuckDB → BigQuery
- DuckDB → Snowflake
- DuckDB → Postgres

**Vector Store**:
- ChromaDB → Vertex Vector Search
- ChromaDB → Cortex Search (Snowflake)
- ChromaDB → OpenSearch

**Compute**:
- FastAPI local → Cloud Run
- FastAPI local → Lambda
- FastAPI local → ECS

### Patrón:
```python
# config.py
class DataLayerConfig:
    def get_connection(self):
        if self.provider == 'duckdb':
            return duckdb.connect('profiles.duckdb')
        elif self.provider == 'bigquery':
            return bigquery.Client()
        elif self.provider == 'snowflake':
            return snowflake.connect(...)

class VectorStoreConfig:
    def get_client(self):
        if self.provider == 'chroma':
            return chromadb.Client()
        elif self.provider == 'vertex':
            return VertexVectorSearch()
```

---

## PHASE 5: Production - Por Cliente

### Decisión:
- GCP → BigQuery + Vertex Vector Search
- AWS → Aurora PG + OpenSearch
- Snowflake → Cortex Search + Snowpark

---

## COST STRUCTURE

```
LOCAL POC:              $0/month
├─ DuckDB             $0 (file-based)
├─ dbt                $0 (OSS)
├─ FastAPI           $0 (OSS)
├─ ChromaDB          $0 (OSS)
├─ LangGraph         $0 (OSS)
└─ Local LLM         $0 (Ollama)

AWS DEMO:            $5-10/month
├─ Lambda            $1 (pay-per-use)
├─ S3                $1 (small data)
├─ Bedrock calls     $2-5 (cached responses)
└─ CloudWatch        $1

GCP INTEGRATION:      $5-10/month
├─ Cloud Run         $2-3 (auto-scaling)
├─ Secret Manager    $1 (free tier)
└─ Cloud Logging     $1

TOTAL MVP:           $10-20/month
```

---

## ENTREGABLES POR PHASE

**Phase 0** (Semana 1):
- [ ] Repo creado con estructura
- [ ] README con setup instructions
- [ ] docker-compose.yml para local dev
- [ ] .env.example documentado

**Phase 1** (Semana 2-3):
- [ ] dbt project con models (staging/intermediate/marts)
- [ ] Profile 360 table con datos ejemplo
- [ ] FastAPI backend conectado a DuckDB
- [ ] ChromaDB RAG index poblada
- [ ] MCP server con 5 tools básicos
- [ ] LangGraph agent conversacional sobre datos
- [ ] End-to-end test: pregunta → agent → response

**Phase 2** (Semana 3-4):
- [ ] Lambda handler en AWS
- [ ] Bedrock integration
- [ ] Deployable ZIP/Docker image
- [ ] CloudWatch logging
- [ ] Demo endpoint público

**Phase 3** (Semana 4):
- [ ] Cloud Run service
- [ ] GCP credentials en Secret Manager
- [ ] AIF369.com integración
- [ ] Health check endpoint

**Phase 4** (Semana 5):
- [ ] Adapter interfaces
- [ ] Deployment guides por cloud
- [ ] Configuration by environment

**Phase 5** (Future):
- [ ] Production architecture doc
- [ ] Security model
- [ ] Cost estimation templates

---

## ¿POR QUÉ ESTE STACK?

**Vendible**:
- Agentic Data Pipelines
- Profile Augmentation
- Enterprise RAG
- MCP Servers
- Modern Data Stack for AI

**Demostrable**:
- "El Androide" en AWS = portfolio técnico
- Local PoC = rápido desarrollo
- Cloud adapters = portabilidad

**Económico**:
- $0 local
- $10-20 en AWS+GCP
- Escalable sin reescribir

**Profesional**:
- dbt (production standard)
- LangGraph (state management)
- MCP (tool interoperability)
- Cloud-portable (no lock-in)

---

## SIGUIENTE PASO: EMPEZAR PHASE 0

¿Vamos con crear la estructura base + sample data?
