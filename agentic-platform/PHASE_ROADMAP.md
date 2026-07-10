# Agentic Platform: Phase Roadmap

**Timeline**: 29 días (Julio 2-31, 2026)

---

## Phase 1: Discovery & Evaluation ✅ (Complete)

**Duration**: Weeks 1-2 (7-14 days)
**Status**: DEPLOYED & SEMI-PRODUCTIVE

### What's Done
- ✅ Sales Concierge Agent (greeting + profiling)
- ✅ Business Discovery Agent (5-question discovery)
- ✅ AI Scorecard 369 Agent (9-dimension evaluation)
- ✅ LangGraph orchestrator with state routing
- ✅ PostgreSQL session persistence
- ✅ BigQuery analytics logging
- ✅ Chat interface (agentic-platform.html)

### Metrics to Track
- Session completion rate (% reaching Scorecard)
- Average conversation length (target: 12-15 turns)
- Time to scorecard (target: 3-5 minutes)
- Visitor → Email capture rate
- Lead quality score distribution

### Deployment Checklist
```
□ Install dependencies: pip install -r requirements.txt
□ Setup .env.local with API keys
□ Create PostgreSQL database
□ Create BigQuery tables
□ Run API: python -m uvicorn api:app --reload
□ Test chat flow end-to-end
□ Deploy to staging
□ Monitor logs in production
```

---

## Phase 2: Architecture & ROI (Weeks 2-3)

**Duration**: 7-10 days
**Goal**: Generate recommendations and business case

### New Agents

#### 1. Knowledge Agent (RAG)
**Purpose**: Provide authoritative guidance based on company knowledge base

**Data Sources**:
- Método 369 documentation
- AI Governance frameworks (NIST AI RMF, ISO 42001, ISO 23894)
- Ley 21.719 (Chilean data protection)
- AI Act (EU regulation)
- DAMA (Data Management Body of Knowledge)
- Internal case studies

**Implementation**:
```python
# Fetch from knowledge base
from langchain_community.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

vector_store = Chroma.load_persisted("./knowledge_base")
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

# Query during conversation
context = retriever.get_relevant_documents(user_query)
```

**Integration**: Used by Architecture Agent when designing solutions

#### 2. Architecture Agent
**Purpose**: Design initial architecture recommendations

**Inputs** (from previous agents):
- Company size + industry
- Current AI maturity
- Critical processes
- Main pain points
- Budget estimate

**Outputs**:
- Cloud platform recommendation (AWS/Azure/GCP)
- Tool stack (Claude, Vertex AI, etc.)
- Data pipeline design
- Deployment timeline
- Estimated team requirements

**Example Output**:
```
RECOMMENDED ARCHITECTURE
━━━━━━━━━━━━━━━━━━━━━━━━

Cloud: AWS (based on existing infrastructure)

Data Layer:
→ S3 for data lake
→ Glue for ETL
→ Athena for queries

AI Layer:
→ Claude API for reasoning
→ SageMaker for custom models
→ Step Functions for orchestration

Deployment: 8 weeks, 3 people

Estimated Cost: $8k/month (infrastructure) + $15k/month (Claude API)
```

#### 3. ROI Agent
**Purpose**: Calculate financial impact

**Calculates**:
- Baseline cost (current state)
- Cost with AI (projected)
- Savings (reduction %)
- Payback period
- 3-year ROI

**Example**:
```
FINANCIAL IMPACT
━━━━━━━━━━━━━━━━━

Current State (Status Quo):
→ 8 people in operations
→ 40 hours/week on manual processing
→ Cost: $200k/month

With AI System:
→ 3 people (5 ops, 1 AI engineer, 1 data scientist)
→ 5 hours/week on manual processing
→ Cost: $80k/month

SAVINGS:
→ Monthly: $120k
→ Annual: $1.44M
→ Payback: 3 months
→ 3-Year ROI: 420%
```

### New Features

#### Proposal Generator
**Input**: All previous agent outputs + user data
**Output**: Markdown/PDF proposal with:
- Executive Brief (1 page)
- Situation Analysis (2 pages)
- Recommended Architecture (3 pages)
- Financial Impact (1 page)
- Implementation Roadmap (2 pages)
- Risk Assessment (1 page)
- Investment (1 page)

#### Google Calendar Integration
**Functionality**:
- Auto-schedule follow-up meeting after scorecard
- Send calendar invite to prospect
- Create internal CRM task for sales team
- Log meeting details to Sheets

**Implementation**:
```python
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

calendar_service = build('calendar', 'v3', credentials=credentials)

# Schedule meeting
event = {
    'summary': f'AIF369 Consultation - {prospect_name}',
    'description': f'AI Scorecard Review & Architecture Discussion\n\nMaturity Score: {scorecard_score}/10',
    'start': {'dateTime': meeting_time.isoformat()},
    'end': {'dateTime': (meeting_time + timedelta(hours=1)).isoformat()},
    'attendees': [{'email': prospect_email}],
}
calendar_service.events().insert(calendarId='primary', body=event).execute()
```

### Phase 2 Deliverables
- [ ] Knowledge Agent with RAG over Método 369
- [ ] Architecture Agent (recommends cloud/tools)
- [ ] ROI Agent (calculates financial impact)
- [ ] Proposal Generator (PDF output)
- [ ] Google Calendar integration
- [ ] Google Sheets lead database
- [ ] Improved routing logic between agents
- [ ] Proposal tracking in CRM

### Metrics to Track
- Proposal generation time (target: <2 minutes)
- Meeting booking rate (% of scores that schedule follow-up)
- Proposal engagement (% opened, time spent)
- Conversion rate (proposal → signed contract)

---

## Phase 3: Orchestration & Production (Weeks 3-4)

**Duration**: 7-10 days
**Goal**: Production-ready multi-agent system with full observability

### Advanced Orchestration

#### 1. Dynamic Agent Selection
Instead of linear flow (Concierge → Discovery → Scorecard → Architecture → ROI → Proposal), system decides which agent is most relevant based on context.

```python
# Router Agent
def route_next_agent(state: PlatformState) -> str:
    # Analyze conversation
    # Decide which agent provides most value next
    # Options: knowledge_agent, architecture_agent, roi_agent, cio_advisor, compliance_agent
    
    if state.stage == "discovery" and user_asked_about_governance:
        return "knowledge_agent"
    elif state.stage == "discovery" and user_asked_about_costs:
        return "roi_agent"
    else:
        return "architecture_agent"
```

#### 2. Parallel Agent Execution
Multiple agents work on different aspects simultaneously (where possible).

```python
# Concurrently:
# - Knowledge Agent queries RAG
# - Architecture Agent designs infrastructure
# - ROI Agent calculates impact
# - Compliance Agent checks Ley 21.719 requirements

tasks = [
    knowledge_agent.invoke(state),
    architecture_agent.invoke(state),
    roi_agent.invoke(state),
    compliance_agent.invoke(state),
]
results = asyncio.gather(*tasks)
```

### MCP Integrations

#### Model Context Protocol Connections
Connect to enterprise tools without custom integrations.

```python
# MCP Servers to integrate:
# - Google Drive (read/write proposals)
# - Slack (send notifications)
# - Notion (CRM updates)
# - Jira (create implementation tasks)
# - GitHub (link to documentation)
```

### Observability

#### Traces
Log every agent invocation with:
- Agent name
- Input tokens
- Output tokens
- Latency
- Cost
- Success/failure

#### Metrics
Dashboard showing:
- Conversation funnel (started → scorecard → proposal → meeting)
- Average score by industry
- Agent performance (how often leads progress)
- Cost per conversation
- Revenue per conversation (post-sales)

#### Evaluations
Automated scoring of agent quality:
- Did Concierge capture all required fields?
- Did Discovery ask all 5 questions?
- Was Scorecard score reasonable given data?
- Was Architecture recommendation relevant?
- Was ROI calculation accurate?

```python
# Evaluation Chain
def evaluate_concierge_quality(messages: list) -> float:
    # Score 0-1
    # Required fields captured?
    # Questions asked in natural way?
    # Transition to next agent smooth?
    pass
```

### Cost Tracking

Track spending per session:
- Claude API tokens
- Google API calls
- Database queries
- Storage

```
Session #12345:
├─ Claude: 8,234 tokens = $0.25
├─ Google Calendar: 1 call = $0.00
├─ Google Sheets: 2 writes = $0.00
├─ Postgres: 45 queries = $0.02
└─ Total: $0.27
```

### Production Deployment

#### Infrastructure
```
Frontend (Vercel):
→ agentic-platform.html
→ Real-time updates
→ Global CDN

Backend (Cloud Run / EC2):
→ FastAPI server
→ Auto-scaling
→ Health checks

Database:
→ Postgres (Cloud SQL)
→ Automated backups
→ Read replicas

Analytics:
→ BigQuery
→ Looker dashboards
→ Real-time monitoring
```

#### Logging & Monitoring
```python
# Structured logging
import structlog
logger = structlog.get_logger()

logger.info("chat_message", session_id=sid, agent="concierge", tokens_used=234)
logger.info("proposal_generated", session_id=sid, file_size=45000, status="success")
```

#### Error Handling
- Retry logic for API failures
- Fallback agents when primary fails
- Error reporting to admin
- User-friendly error messages

### Phase 3 Deliverables
- [ ] Multi-Agent Orchestrator (dynamic routing)
- [ ] Parallel agent execution
- [ ] MCP integrations (Slack, Notion, Drive, etc.)
- [ ] Observability dashboard (traces + metrics)
- [ ] Cost tracking per conversation
- [ ] Automated evaluations of agent quality
- [ ] Production deployment pipeline
- [ ] Error handling + fallback logic
- [ ] Admin dashboard for monitoring
- [ ] API rate limiting + quota management

### Metrics to Track
- Uptime (target: 99.9%)
- P50/P95/P99 latency (target: <3s, <8s, <15s)
- Cost per conversation (track: tokens, API calls, storage)
- Agent success rate (% of conversations that complete)
- User satisfaction (NPS/CSAT from follow-up)

---

## Success Criteria (End of Month)

```
✅ Phase 1 (Week 1-2): 
   - Platform deployed and semi-productive
   - Real prospects using it
   - Conversations being saved to Postgres
   - Scorecards being generated

✅ Phase 2 (Week 2-3):
   - Proposals being generated
   - Follow-up meetings being scheduled
   - Leads being qualified
   - ROI being calculated per prospect

✅ Phase 3 (Week 3-4):
   - Full multi-agent orchestration working
   - Observability dashboard live
   - Cost tracking accurate
   - System handling 10+ concurrent sessions
   - Ready for pitch/demo to investors
```

---

## Demo Script (End of Month)

```
"Here's our Agentic Sales Platform. It's built with Claude, LangGraph, and MCP.

When a prospect visits, the Sales Concierge greets them and captures basic info.
Then the Discovery Agent asks 5 deep questions about their business.
Once we have context, the Scorecard Agent evaluates their AI maturity across 9 dimensions.
Then the Architecture Agent recommends a specific tech stack.
The ROI Agent calculates expected financial impact.
Finally, we generate a complete proposal with executive brief, roadmap, and financial model.

All of this happens in 5 minutes. No human required.

The system learns from every conversation. We track which questions work best,
which recommendations convert to sales, and which offers prospects accept.

This platform demonstrates: multi-agent orchestration, RAG, MCP integrations,
cost tracking, observability, and production-ready AI systems.

We're seeing X% of prospects go from discovery to scheduled meeting."
```

---

## Weekly Milestones

| Week | Dates | Milestones |
|------|-------|-----------|
| 1 | Jul 2-8 | Phase 1 deployed, real prospects using it |
| 2 | Jul 9-15 | Phase 2 (proposals + ROI) working, integrations starting |
| 3 | Jul 16-22 | Phase 3 orchestration complete, observability live |
| 4 | Jul 23-29 | Production hardening, testing, performance tuning |
| Demo | Jul 30-31 | Final polish, run through full demo script |

---

## Known Limitations (Phase 1-3)

- Proposal generation is markdown (PDF conversion in Phase 3.5)
- No video/image content in proposals (text-only)
- MCP integrations are read-only in Phase 2 (write in Phase 3)
- No custom branding in generated proposals (template-based)
- Memory is per-conversation (no cross-session learning yet)

These can be addressed in post-launch sprints.
