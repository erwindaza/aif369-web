# Testing Phase 1 + Phase 2

Guide to test the complete agentic platform flow.

## Quick Start

### 1. Install Dependencies

```bash
cd agentic-platform
pip install -r requirements.txt
```

### 2. Setup Environment

```bash
cat > .env.local << EOF
ANTHROPIC_API_KEY=your_anthropic_key
DATABASE_URL=postgresql://user:password@localhost/aif369_platform
PROJECT_ID=aif369-backend
DATASET_ID=aif369_analytics
GOOGLE_API_KEY=your_google_key
EOF
```

### 3. Create Database

```bash
createdb aif369_platform
```

### 4. Run Test Script

```bash
python test_phase1_2.py
```

This will:
1. ✅ Concierge Agent - Greet and profile
2. ✅ Discovery Agent - Ask 5 deep questions
3. ✅ Scorecard Agent - Evaluate maturity
4. ✅ Architecture Agent - Design infrastructure
5. ✅ ROI Agent - Calculate financial impact
6. ✅ Proposal Generator - Create complete proposal

## Test Flow

The test conversation simulates a real prospect journey:

```
Turn 1: User introduces themselves (CDO at Falabella)
Turn 2-6: Discovery questions about AI maturity, processes, pain points
Turn 7: Request for proposal

Expected output:
- Captured profile (name, email, company, role)
- AI Scorecard 369 (9 dimensions evaluated)
- Architecture recommendation (AWS/Azure/GCP + stack)
- ROI analysis (monthly savings, payback, 3-year ROI)
- Complete proposal document (markdown)
```

## Expected Output

```
================================================================================
🤖 AGENTIC PLATFORM - TESTING PHASE 1 + PHASE 2
================================================================================

[Turn 1] User: Hola, me llamo Juan Pérez y trabajo en Falabella como CDO
---
[Assistant] ¡Hola Juan! Soy el Sales Concierge de AIF369...
Stage: discovery
Current Agent: concierge

[Turn 2] User: Diría que nuestro AI está en un 4/10
---
[Assistant] Perfecto, Juan. Ahora voy a hacer algunas preguntas...
Stage: discovery
Current Agent: discovery

...

[Turn 7] User: Genera mi propuesta
---
[Assistant] 📄 PROPUESTA COMERCIAL GENERADA
Tu propuesta completa está lista. Incluye:
✅ Executive Brief
✅ Evaluación de Madurez (Scorecard 369)
✅ Arquitectura Recomendada
✅ Análisis Financiero (ROI)
✅ Plan de Implementación
✅ Términos Comerciales

================================================================================
✅ CONVERSATION COMPLETE
================================================================================

📊 FINAL STATE:
{
  "session_id": "test_phase1_2_20260702_120000",
  "name": "Juan Pérez",
  "company": "Falabella",
  "email": "juan@falabella.com",
  "role": "CDO",
  "overall_maturity": 5,
  "stage": "proposal_generated",
  "scorecard": {
    "AI Strategy": 4,
    "AI Governance": 3,
    "Risk Management": 4,
    ...
  },
  "total_turns": 14
}

📄 PROPOSAL GENERATED:
# PROPUESTA COMERCIAL AIF369
...
```

## Testing Checklist

### Phase 1: Discovery & Evaluation
- [ ] Concierge captures name, email, company, role
- [ ] Discovery asks all 5 questions
- [ ] Scorecard evaluates 9 dimensions correctly
- [ ] Maturity score is reasonable (0-10)
- [ ] User can move through flow without issues

### Phase 2: Architecture & ROI
- [ ] Architecture Agent generates reasonable recommendations
- [ ] Architecture includes: cloud platform, data layer, AI layer, timeline, cost
- [ ] ROI Agent calculates baseline, savings, payback period
- [ ] ROI numbers are realistic (not too optimistic)
- [ ] Proposal Generator creates well-structured document
- [ ] Proposal includes all sections: brief, scorecard, architecture, ROI, roadmap, terms

### Integration
- [ ] All messages are persisted to Postgres
- [ ] Conversation logs to BigQuery
- [ ] Session state is maintained across turns
- [ ] Error handling works (graceful fallbacks)
- [ ] Timing is reasonable (<5s per turn for Claude calls)

## Troubleshooting

### ImportError: No module named 'langgraph'
```bash
pip install langgraph==0.0.50
```

### Database connection error
```bash
# Check Postgres is running
psql -U postgres -c "SELECT 1"

# Create database if missing
createdb aif369_platform
```

### Claude API errors
- Check ANTHROPIC_API_KEY is set
- Verify API key is valid (in Anthropic dashboard)
- Check rate limits haven't been exceeded

### Async/await errors
- Ensure Python 3.8+
- Update asyncio: `pip install --upgrade asyncio`

## Performance Notes

**Expected timings**:
- Concierge turn: ~1-2 seconds
- Discovery turns: ~2-3 seconds each
- Scorecard turn: ~3-4 seconds
- Architecture turn: ~4-5 seconds
- ROI turn: ~4-5 seconds
- Proposal turn: ~5-6 seconds

**Total conversation time**: ~5-7 minutes for complete flow

## Next Steps

After testing Phase 1 + 2:

1. **Iterate on prompts** - Refine agent instructions based on output quality
2. **Add more scoring logic** - Replace simple keyword matching with Claude evaluation
3. **Integrate Google Calendar** - Auto-schedule follow-up meetings
4. **Add CRM integration** - Push leads to Google Sheets
5. **Deploy to staging** - Test with real users

## Manual Testing

To test individual agents:

```python
from orchestrator import orchestrator
from config import PlatformState

# Create initial state
state = {
    "session_id": "manual_test_1",
    "messages": [],
    # ... other fields
}

# Run through graph
result = orchestrator.graph.invoke(state)
print(result["messages"][-1])
```

## Questions?

Check:
- `README.md` - Architecture overview
- `PHASE_ROADMAP.md` - Full roadmap
- `config.py` - Configuration + state definition
