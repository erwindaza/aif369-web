# AIF369 Agentic Sales Platform

Multi-agent AI system for automated discovery, evaluation, and proposal generation.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Client (agentic-platform.html)               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    /api/chat (FastAPI)
                             │
                    ┌────────▼────────┐
                    │  Orchestrator   │
                    │  (LangGraph)    │
                    └────────┬────────┘
                    │        │        │
        ┌───────────▼┐  ┌───▼───────┐  ┌────────────┐
        │ Concierge  │  │ Discovery │  │ Scorecard  │
        │   Agent    │  │   Agent   │  │   Agent    │
        └────────────┘  └───────────┘  └────────────┘
                             │
                    ┌────────▼────────┐
                    │  Persistence    │
                    ├─────────────────┤
                    │ PostgreSQL      │
                    │ BigQuery (logs) │
                    │ Google Sheets   │
                    │ Google Calendar │
                    └─────────────────┘
```

## Setup

### 1. Environment Variables

```bash
cat > .env.local << EOF
ANTHROPIC_API_KEY=your_key_here
DATABASE_URL=postgresql://user:password@localhost/aif369_platform
PROJECT_ID=aif369-backend
DATASET_ID=aif369_analytics
GOOGLE_API_KEY=your_google_key
GOOGLE_CALENDAR_ID=your_calendar_id
GOOGLE_SHEETS_ID=your_sheets_id
EOF
```

### 2. Install Dependencies

```bash
cd agentic-platform
pip install -r requirements.txt
```

### 3. Setup Database

```bash
# Create PostgreSQL database
createdb aif369_platform

# Create tables (runs automatically on API startup)
python -m api
```

### 4. Run API Server

```bash
cd agentic-platform
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Access Platform

Open browser to: `http://localhost:3000/agentic-platform.html`

## Agents

### 1. Sales Concierge
**Role**: Initial contact and warm-up
- Greets prospect
- Captures name, email, company, role
- Identifies urgency
- Routes to Discovery Agent

**System Prompt**: See `config.py`

### 2. Business Discovery
**Role**: Deep-dive into business context
- Asks 5 structured questions
- Identifies critical processes
- Uncovers main pain points
- Assesses AI maturity baseline

**Questions**:
1. Current AI maturity (1-10)
2. Critical processes
3. Main pain points
4. Priorities
5. Team/data availability

### 3. AI Scorecard 369
**Role**: Formal maturity evaluation
- Evaluates 9 dimensions:
  1. AI Strategy
  2. AI Governance
  3. Risk Management
  4. Data Quality
  5. AI Factory Design
  6. Observability
  7. Ethics & Responsible AI
  8. Regulation & Compliance
  9. Talent & Culture

- Scores each 1-10
- Generates executive summary
- Interprets findings

## Persistence

### PostgreSQL
Stores:
- Conversation history
- User profiles
- Session state
- Scorecard results

### BigQuery
Logs:
- All conversations (for analytics)
- Agent performance metrics
- Lead scoring
- Engagement metrics

### Google Integrations
- **Google Calendar**: Schedule follow-up meetings
- **Google Sheets**: Lead database
- **Google Drive**: Store proposals (Phase 2)

## Phase Roadmap

### Phase 1 (Week 1-2) ✅ Current
- [x] Sales Concierge Agent
- [x] Business Discovery Agent
- [x] AI Scorecard 369 Agent
- [x] Basic persistence (PostgreSQL)
- [x] BigQuery logging
- [x] Frontend chat interface

### Phase 2 (Week 2-3)
- [ ] Knowledge Agent (RAG over Método 369 + regulations)
- [ ] Architecture Agent (design recommendations)
- [ ] ROI Agent (calculate financial impact)
- [ ] Proposal Generator (executive brief, roadmap)
- [ ] Google Calendar integration (auto-schedule)

### Phase 3 (Week 3-4)
- [ ] Multi-Agent Orchestrator improvements
- [ ] Observability (traces, costs, metrics)
- [ ] Evaluations (agent performance scoring)
- [ ] Memory enhancements
- [ ] MCP integrations (Slack, Jira, Notion)
- [ ] Production deployment

## API Endpoints

### POST /api/chat
```json
{
  "session_id": "session_xxx",
  "user_input": "User message here"
}
```

Response:
```json
{
  "session_id": "session_xxx",
  "conversation_id": "conv_xxx",
  "agent": "concierge",
  "messages": [...],
  "stage": "discovery",
  "name": "...",
  "company": "...",
  "email": "...",
  "overall_maturity": 5
}
```

### GET /api/session/{session_id}
Retrieve full conversation state

## Development

### Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

### Testing Agents
```python
from orchestrator import orchestrator

state = {
    "session_id": "test_123",
    "messages": [],
    # ... other fields
}

result = orchestrator.graph.invoke(state)
print(result["messages"][-1])
```

## Performance Notes

- Chat latency: ~2-3s (Claude API + LangGraph)
- Concurrent sessions: Limited by Postgres connection pool (adjust `max_connections`)
- BigQuery: Batches writes every 100 events or 30 seconds

## Next Steps

1. **Week 1**: Deploy Phase 1, test with real prospects
2. **Week 2**: Gather feedback, refine prompts, build Phase 2
3. **Week 3**: Integrate Google APIs, add proposal generation
4. **Week 4**: Performance tuning, observability, production readiness

## Support

Contact: edaza@aif369.com
