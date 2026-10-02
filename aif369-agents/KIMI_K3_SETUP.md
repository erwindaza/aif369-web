# Kimi K3 Setup para DAMABOOK Agent

Kimi K3 es un modelo multimodal agentic de Moonshot AI disponible en Ollama Cloud.

## Prerequisitos

- Ollama instalado
- Ollama Pro o Max subscription (para acceso a Kimi K3)
- ~10GB de espacio

## Instalación de Kimi K3

### Opción 1: Usar Ollama Cloud (Recomendado)

```bash
# Lanuch Kimi K3 desde cloud
ollama launch --model kimi-k3:cloud

# Verificar que está corriendo
curl http://localhost:11434/api/tags
```

### Opción 2: Descargar localmente (Si tienes capacidad)

```bash
ollama pull kimi-k3

# Verificar
ollama list | grep kimi
```

## Configuración en Docker

El docker-compose.test.yml ya está configurado para usar Kimi K3.

```yaml
# En docker-compose.test.yml:
orchestrator:
  environment:
    - OLLAMA_HOST=http://ollama:11434
```

El DAMABOOK Agent intentará usar Kimi K3. Si no está disponible, fallback a Mistral 7B automáticamente.

## Testeando DAMABOOK Agent

```bash
# Terminal 1: Levantar containers
docker-compose -f docker-compose.test.yml up

# Terminal 2: Correr tests
python tests/test_agents.py

# Test 3 específicamente para DAMABOOK
# Debería usar Kimi K3 y responder sobre Ley 21.719
```

## Ejemplos de Queries para DAMABOOK

```bash
# Clasificación - debería detectar como "damabook"
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Cómo cumplo con Ley 21.719?"}'

# Auto-routing a DAMABOOK
curl -X POST http://localhost:8000/submit_auto \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Necesito entender los derechos del titular en protección de datos",
    "customer_phone": "+56912345678"
  }'

# Consulta sobre gobernanza
curl -X POST http://localhost:8000/submit_auto \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Queremos implementar data governance en nuestra organización",
    "customer_phone": "+56987654321"
  }'
```

## Capacidades de DAMABOOK con Kimi K3

### Multimodal Analysis
- Analizar documentos PDF/imágenes
- Revisar políticas de privacidad
- Validar contratos
- Estructuras de datos complejas

### Ley 21.719 Expertise
- Derechos del titular (acceso, rectificación, supresión, oposición, portabilidad)
- Obligaciones organizacionales
- Cumplimiento de términos
- Evaluación de brechas

### Servicios Ofrecidos
1. **Data Governance Audit** ($3k USD)
   - Análisis de datos actuales
   - Mapeo de procesamiento
   - Evaluación Ley 21.719
   - Reporte de gaps

2. **Ley 21.719 Compliance Plan** ($5k USD)
   - Plan de acción detallado
   - Políticas de privacidad
   - Templates de consentimiento
   - Procedimientos de seguridad

3. **Data Quality Framework** ($4k USD)
   - Framework de calidad
   - Métricas de datos
   - Validación y limpieza
   - Monitoreo continuo

4. **Ongoing Support** ($2k USD/month)
   - Monitoreo de cumplimiento
   - Actualizaciones normativas
   - Soporte técnico
   - Reportes mensuales

## Fallback Strategy

Si Kimi K3 no está disponible:
- DAMABOOK automáticamente usa Mistral 7B
- Sigue respondiendo preguntas sobre Ley 21.719
- Funcionalidad completa (solo sin análisis multimodal de imágenes)

```python
# En damabook_agent.py:
try:
    self.model_name = "kimi-k3:cloud"
except:
    self.logger.warning("Kimi K3 not available, using mistral:7b")
    self.model_name = "mistral:7b"
```

## Escalación a LEGAL Agent (Futuro)

DAMABOOK detecta si pregunta es compleja y escalala a LEGAL:
- Sanciones/multas
- Responsabilidad legal
- Demandas/litigios
- Interpretaciones legales complejas

```
Customer → "¿Qué pasa si no cumplo Ley 21.719?"
           ↓
DAMABOOK: Detecta complejidad legal
           ↓
Escalada a LEGAL Agent (cuando esté disponible)
```

## Troubleshooting

### "Kimi K3 not found"
```bash
# Verificar que Ollama está corriendo
ollama list

# Si no aparece Kimi K3:
# 1. Verifica que tienes Pro/Max subscription en Ollama
# 2. Ejecuta: ollama launch --model kimi-k3:cloud
# 3. Por ahora usará Mistral 7B como fallback
```

### "Connection refused"
```bash
# Asegúrate que Ollama está activo
ollama serve &

# Verifica puerto
lsof -i :11434
```

### "Memory issues"
```bash
# Kimi K3 requiere más memoria que Mistral
# Si tienes problemas:
# 1. Cierra otras aplicaciones
# 2. Aumenta memoria disponible para Docker
# 3. Fallback a Mistral es automático
```

---

**Estado Actual:** DAMABOOK Agent listo con Kimi K3 (fallback a Mistral)
**Tests:** Incluye TEST 3 para DAMABOOK
**Próximo:** LEGAL Agent + escalación entre agentes
