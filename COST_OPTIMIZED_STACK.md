# AIF369 - Stack Económico para MVP/Startup

**Objetivo**: Montar IA funcional sin gastar $2-5k/mes
**Budget real**: $0-300/mes

---

## OPCIÓN 1: 100% GRATIS (Local + Open Source) ⭐ RECOMENDADO PARA EMPEZAR

### Tech Stack:
```
Frontend:     HTML + JS (local)
Backend:      FastAPI (Python, gratis)
LLM:          Ollama + Llama 3.1 (local, gratis)
Database:     SQLite (gratis, 0 operaciones)
Hosting:      Tu máquina (mientras desarrollas)
```

### Costo: $0/mes
### Tiempo setup: 2 horas

### Pasos:

**1. Instalar Ollama + Llama 3.1**
```bash
# Descargar Ollama (gratis)
brew install ollama

# Descargar Llama 3.1 (gratis, 5GB)
ollama pull llama2

# Correr local
ollama serve
# Ahora disponible en http://localhost:11434
```

**2. Usar Ollama en lugar de Claude API**
```python
# En lugar de:
from anthropic import Anthropic
client = Anthropic()

# Hace esto:
import ollama

response = ollama.generate(
    model="llama2",
    prompt="Tu pregunta aquí",
)
print(response['response'])

# COSTO: $0 (corre en tu máquina)
# LATENCY: 2-5 seg/response (dependiendo tu CPU)
```

**3. Base de datos local**
```python
# SQLite (no necesita servidor)
import sqlite3

conn = sqlite3.connect('aif369.db')  # Archivo local, done
cursor = conn.cursor()

# Mismo SQL que Postgres, pero gratis
cursor.execute('''
    CREATE TABLE conversations (
        session_id TEXT,
        messages JSON,
        created_at TEXT
    )
''')
```

### Limitaciones:
- ❌ Latency: 2-5 segundos (vs 500ms con APIs)
- ❌ Calidad: Llama 3.1 es 80% de Claude (pero gratis)
- ✅ Escalabilidad: Solo para dev/testing (100 users max)
- ✅ Costo: CERO

### Cuándo cambiar: Cuando tengas 50+ usuarios reales

---

## OPCIÓN 2: HYBRID (Mostly Free) - LO MÁS PRÁCTICO

### Tech Stack:
```
Frontend:     HTML + JS (gratis)
Backend:      FastAPI en Render.com ($7/mes)
LLM:          Groq + Together.ai (freemium)
Database:     PostgreSQL en Railway ($7/mes)
Hosting:      Render (PaaS barato)
```

### Costo: $14-30/mes
### Tiempo setup: 4-5 horas
### Calidad: 95% vs Claude, pero 50x más barato

### Pasos:

**1. API Gratuitas de Alta Calidad (FREEMIUM)**

**Groq** (RECOMENDADO - muy rápido y gratis)
```bash
# Signup: https://console.groq.com/
# 1. Get free API key
# 2. 10k requests/día GRATIS (suficiente para MVP)
# 3. Modelo: Llama 2, Mixtral (muy bueno)

pip install groq

# Python:
from groq import Groq

client = Groq(api_key="gsk_...")

response = client.chat.completions.create(
    model="mixtral-8x7b-32768",  # Gratis
    messages=[{"role": "user", "content": "..."}],
)

print(response.choices[0].message.content)

# COSTO: $0/mes (primeros 10k requests)
# VELOCIDAD: 50ms (MÁS RÁPIDO que Claude)
# CALIDAD: 90% (Mixtral es muy bueno)
```

**Together.ai** (Fallback / Complementario)
```bash
# https://together.ai
# 3 free trial credits = 300k tokens gratis
# Después: $0.001/1k tokens (vs $0.075 con Gemini)

from together import Together

client = Together(api_key="...")

response = client.chat.completions.create(
    model="meta-llama/Llama-2-70b-chat-hf",
    messages=[...],
)
```

**Replicate** (para tareas específicas)
```
# https://replicate.com
# 1. Signup gratis
# 2. $0.0005 por prediction (tiny)
# 3. Usa modelos open source

# Para: OCR, image classification, etc.
# Costo: $0 (si usas <100 predictions/mes)
```

**2. Hosting Super Barato**

**Render.com** (mejor que Heroku ahora)
```bash
# 1. Deploy Flask/FastAPI
# 2. Free tier: $0/mes (limitado)
# 3. Starter tier: $7/mes (mejor)
# 4. PostgreSQL: $7/mes

# 1 API server + 1 DB = $14/mes total
```

**Vercel** (para frontend)
```bash
# Gratis forever
# Deploy HTML + JS
# CDN global incluido
```

**Railway.app** (alternativa a Render)
```bash
# $5/mes credit gratis
# Después: pay-as-you-go
# Muy barato para bajo uso
```

**3. Base de datos super barata**

**Supabase** (PostgreSQL managado, barato)
```bash
# Free tier:
# - 500MB storage
# - 2GB bandwidth/mes
# - Suficiente para MVP

# Cost: $0-25/mes
```

O simplemente **Railway + PostgreSQL** ($7/mes)

### Precio Total:
```
Groq API:           $0   (free tier 10k requests)
Render backend:     $7   (starter)
Railway PostgreSQL: $7   (shared)
Vercel frontend:    $0   (gratis)
─────────────────────────
TOTAL/mes:         $14
```

### Calidad/Performance:
```
LLM Quality:  90-95% vs Claude (Mixtral/Llama 70B)
Speed:        50-200ms (Groq es RÁPIDO)
Scalability:  100-1000 users (con Render)
Uptime:       99.9%
```

---

## OPCIÓN 3: ULTRA-ECONÓMICA PARA PRODUCCIÓN

### Stack:
```
LLM:          Groq (gratis) + fallback open-source
Database:     SQLite en Railway ($0-7/mes)
Backend:      FastAPI en Railway ($0-7/mes)
Frontend:     Vercel ($0)
Monitoring:   Sentry free tier ($0)
```

### Costo: $0-14/mes

### Flujo Real:
```
Usuario pregunta
    ↓
FastAPI en Railway
    ↓
Intenta Groq (gratis) ← Éxito 99% de las veces
    ↓
Si falla, fallback a Ollama local o Together.ai
    ↓
SQLite en Railway
    ↓
Respuesta al usuario

Costo por 1000 requests: $0.10 (si todos usan fallback)
```

---

## COMPARATIVA: Todas las opciones

| Opción | Costo/mes | LLM Quality | Speed | Setup | Escalabilidad |
|--------|-----------|------------|-------|-------|---------------|
| **1. Local** | $0 | 80% | 2-5s | 2h | 100 users |
| **2. Groq Hybrid** ⭐ | $14 | 90% | 50ms | 4h | 1000 users |
| **3. SelfHosted** | $7-30 | 85% | 1-3s | 6h | 500 users |
| Claude (Baseline) | $5000 | 100% | 500ms | 1h | ∞ |
| Gemini 2.5 Flash | $2000 | 95% | 300ms | 1h | ∞ |

---

## MI RECOMENDACIÓN PARA AIF369

### **Fase 1: MVP (Primeros 3 meses)**
```
✅ Usar Groq (freemium)
   - 10k requests/día gratis
   - Suficiente para <100 usuarios
   - Costo: $0/mes
   
✅ SQLite local (mientras debugeas)
   - Deploy a Railway después
   
✅ Vercel para frontend
   - Gratis, global CDN
   
✅ Testing: Usa Ollama local (gratis)

COSTO: $0-7/mes
```

### **Fase 2: PMF (Después que valides)**
```
✅ Cuando tengas 100+ usuarios:
   - Activa Render Backend ($7)
   - PostgreSQL en Railway ($7)
   - Groq sigue gratis (o $1-5/mes si superas 10k/día)
   
COSTO: $14-20/mes
```

### **Fase 3: Scale (10k+ usuarios)**
```
✅ Entonces sí, considera Claude/Gemini
   - Pero solo cuando AI sea core revenue driver
   - A esa escala, $5k/mes es peanuts
   
COSTO: $5k/mes (pero ganando 10x eso)
```

---

## SETUP ACTUAL PARA PROBAR AHORA

```bash
# 1. Instalar Ollama (gratis)
brew install ollama
ollama pull llama2
ollama serve

# 2. Modificar orchestrator.py para usar Ollama
# (en lugar de Anthropic)

# 3. Test local
cd agentic-platform
python test_phase1_2.py

# COSTO: $0
# TIEMPO: 30 minutos
```

### Código para cambiar a Ollama:

**Antes** (agentic-platform/config.py):
```python
from anthropic import Anthropic
client = Anthropic()
```

**Después**:
```python
import ollama

def call_llm(prompt, system=""):
    response = ollama.generate(
        model="llama2",
        prompt=prompt,
        system=system,
    )
    return response['response']
```

### Performance esperado:
```
Groq:     50-100ms (mejor)
Ollama:   2-5s (local, pero gratis)
Claude:   300-500ms
```

---

## PROS vs CONS

### Opción 1: Local Ollama ($0)
```
✅ Gratis forever
✅ Sin latency de internet
✅ Funciona offline
❌ Latency alto (2-5s)
❌ Baja calidad (Llama 2 vs Claude 3.5)
❌ Solo para 1-10 usuarios
✅ MEJOR PARA: Desarrollo inicial, testing
```

### Opción 2: Groq Hybrid ($14/mes)
```
✅ Gratis para 10k requests/día
✅ Muy rápido (50ms)
✅ Buena calidad (Mixtral)
✅ Escalable a 1000 users
✅ Sencillo de setup
❌ Pequeño límite free (10k/día)
✅ MEJOR PARA: MVP, primeros clientes
```

### Opción 3: Self-hosted ($7-30/mes)
```
✅ Control total
✅ Costo predecible
✅ Buena escala (500 users)
❌ Más complejo setup
❌ Latency mayor (1-3s)
✅ MEJOR PARA: Cuando tienes budget pequeño pero consistente
```

---

## DECISIÓN FINAL RECOMENDADA

**Si tienes $0 disponibles AHORA:**
```
1. Instala Ollama local (gratis)
2. Testea Phase 1+2 con Llama 2
3. Cuando funcione: Deploy a Groq (gratis)
4. COSTO: $0 forever mientras < 10k requests/día
```

**Si puedes gastar $14/mes:**
```
1. Groq API (freemium)
2. Render backend ($7)
3. Railway DB ($7)
4. COSTO: $14/mes
5. ESCALA: 1000+ users
6. VELOCIDAD: 50ms vs 2-5s con Ollama
```

**Si puedes gastar $100/mes:**
```
1. Groq (paga plan, más límites)
2. Render Pro
3. CloudFlare (DDoS protection)
4. Datadog (monitoring)
5. COSTO: $50-100/mes
6. ESCALA: 10k users
7. UPTIME: 99.99%
```

---

## PRÓXIMOS PASOS

### Ahora (HOY):
```bash
1. pip install ollama
2. ollama pull llama2
3. ollama serve
4. Edita config.py para usar Ollama en lugar de Claude
5. python test_phase1_2.py
6. COSTO: $0
```

### Luego (cuando funcione):
```bash
1. Signup a Groq.com (gratis)
2. Get API key
3. Reemplaza Ollama con Groq client
4. Testea de nuevo
5. COSTO: $0 (gratis tier)
```

### Cuando tengas clientes reales:
```bash
1. Deploy a Render ($7)
2. Deploy a Railway DB ($7)
3. Monitor con Sentry free
4. COSTO: $14/mes
```

---

## RESUMEN: Costo Escalable

```
Users:      1-10        50        100       1000      10k+
────────────────────────────────────────────────────────────
Ollama:     $0          ❌        ❌        ❌        ❌
Groq:       $0          $0        $0        $5        $50
Groq+Rails $0          $14       $14       $20       $100
Claude:     $5000       $5000     $5000     $5000     $5000

✅ Pick Groq for MVP = best cost/quality ratio
```

---

**¿Vamos con Ollama local ahora? (30 min, $0)**

O prefieres **Groq** (4 horas, $0 de cost luego)?
