"""
FastAPI Backend for Agentic Platform
Handles conversation sessions, persistence, and integrations
"""

import os
import json
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from google.cloud import bigquery

from orchestrator import orchestrator
from config import POSTGRES_URL, BIGQUERY_PROJECT, BIGQUERY_DATASET, ADMIN_EMAIL

# FastAPI app
app = FastAPI(title="AIF369 Agentic Platform", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://aif369.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
engine = create_engine(POSTGRES_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class ConversationSession(Base):
    """Store conversation history"""
    __tablename__ = "conversations"

    session_id = Column(String, primary_key=True)
    conversation_id = Column(String, unique=True)
    name = Column(String)
    email = Column(String)
    company = Column(String)
    role = Column(String)
    current_ai_maturity = Column(Integer)
    overall_maturity = Column(Integer)
    stage = Column(String)  # discovery, scoring, architecture, proposal, closed
    messages = Column(JSON)
    scorecard_scores = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Create tables
Base.metadata.create_all(engine)

# BigQuery client
bq_client = bigquery.Client(project=BIGQUERY_PROJECT)


# Pydantic models
class ChatMessage(BaseModel):
    """User message"""
    session_id: str
    user_input: str


class ChatResponse(BaseModel):
    """Assistant response"""
    session_id: str
    conversation_id: str
    agent: str
    messages: list
    stage: str
    name: str
    company: str
    email: str
    overall_maturity: int


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "aif369-agentic-platform"}


@app.post("/api/chat")
async def chat(message: ChatMessage):
    """Process chat message and run orchestrator"""

    db = SessionLocal()

    try:
        # Get or create session
        session = db.query(ConversationSession).filter_by(
            session_id=message.session_id
        ).first()

        if session:
            # Load existing conversation state
            current_state = {
                "session_id": session.session_id,
                "conversation_id": session.conversation_id,
                "name": session.name,
                "email": session.email,
                "company": session.company,
                "role": session.role,
                "current_ai_maturity": session.current_ai_maturity,
                "overall_maturity": session.overall_maturity,
                "messages": session.messages or [],
                "scorecard_scores": session.scorecard_scores or {},
                "stage": session.stage,
                "created_at": session.created_at.isoformat(),
                "last_update": datetime.utcnow().isoformat(),
            }
        else:
            # New session
            current_state = None

        # Run orchestrator
        result = await orchestrator.run_conversation(
            message.session_id,
            message.user_input,
            current_state,
        )

        # Save to database
        if session:
            session.name = result.get("name", "")
            session.email = result.get("email", "")
            session.company = result.get("company", "")
            session.role = result.get("role", "")
            session.current_ai_maturity = result.get("current_ai_maturity", 0)
            session.overall_maturity = result.get("overall_maturity", 0)
            session.messages = result.get("messages", [])
            session.scorecard_scores = result.get("scorecard_scores", {})
            session.stage = result.get("stage", "discovery")
            session.updated_at = datetime.utcnow()
            db.commit()
        else:
            session = ConversationSession(
                session_id=result.get("session_id", str(uuid.uuid4())),
                conversation_id=result.get("conversation_id", str(uuid.uuid4())),
                name=result.get("name", ""),
                email=result.get("email", ""),
                company=result.get("company", ""),
                role=result.get("role", ""),
                current_ai_maturity=result.get("current_ai_maturity", 0),
                overall_maturity=result.get("overall_maturity", 0),
                stage=result.get("stage", "discovery"),
                messages=result.get("messages", []),
                scorecard_scores=result.get("scorecard_scores", {}),
            )
            db.add(session)
            db.commit()

        # Log to BigQuery
        await log_to_bigquery(result)

        return ChatResponse(
            session_id=session.session_id,
            conversation_id=session.conversation_id,
            agent=result.get("current_agent", "unknown"),
            messages=result.get("messages", []),
            stage=result.get("stage", "discovery"),
            name=result.get("name", ""),
            company=result.get("company", ""),
            email=result.get("email", ""),
            overall_maturity=result.get("overall_maturity", 0),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Retrieve conversation session"""

    db = SessionLocal()

    try:
        session = db.query(ConversationSession).filter_by(
            session_id=session_id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": session.session_id,
            "conversation_id": session.conversation_id,
            "name": session.name,
            "email": session.email,
            "company": session.company,
            "role": session.role,
            "stage": session.stage,
            "overall_maturity": session.overall_maturity,
            "scorecard_scores": session.scorecard_scores,
            "messages": session.messages,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }

    finally:
        db.close()


async def log_to_bigquery(state: dict):
    """Log conversation to BigQuery for analytics"""

    try:
        table_id = f"{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}.agentic_platform_conversations"

        row = {
            "session_id": state.get("session_id"),
            "conversation_id": state.get("conversation_id"),
            "timestamp": datetime.utcnow().isoformat(),
            "name": state.get("name", ""),
            "email": state.get("email", ""),
            "company": state.get("company", ""),
            "role": state.get("role", ""),
            "stage": state.get("stage", ""),
            "current_agent": state.get("current_agent", ""),
            "overall_maturity": state.get("overall_maturity", 0),
            "scorecard_scores": json.dumps(state.get("scorecard_scores", {})),
            "message_count": len(state.get("messages", [])),
        }

        bq_client.insert_rows_json(table_id, [row])

    except Exception as e:
        print(f"BigQuery logging error: {e}")
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
