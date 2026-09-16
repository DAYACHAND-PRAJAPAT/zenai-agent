"""
app.py
FastAPI entrypoint for the ZenAI Agent. Exposes the three minimum functional
request types from the assignment (section 5):
  - POST /chat                -> AI Chat (RAG-backed sustainability Q&A)
  - POST /analyze-document     -> Document Analysis (upload + analyze)
  - GET  /regulatory-radar/run -> Regulatory Monitoring
  - GET  /dashboard/requests   -> Review Interface data feed
"""

import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from orchestrator import handle_request
from regulatory_radar import run_regulatory_radar
from ingestion import ingest_file
from embeddings import upsert_chunks
from db.database import init_db, log_request, get_recent_requests

app = FastAPI(title="ZenAI Agent", version="1.0.0")

# Allow the Netlify-hosted frontend to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://zenai-agent.netlify.app/", "http://localhost:5173"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {"status": "ok", "service": "ZenAI Agent", "environment": settings.ENVIRONMENT}


@app.post("/chat")
def chat(payload: ChatRequest):
    """AI Chat: ask a sustainability/environment question, get a cited answer."""
    result = handle_request(payload.message, has_uploaded_document=False)
    log_id = log_request(result)

    return {
        "log_id": log_id,
        "request": result.request_text,
        "in_scope": result.scope_result.in_scope,
        "scope_reason": result.scope_result.reason,
        "matched_keywords": result.scope_result.matched_keywords,
        "request_type": result.request_type,
        "model_used": result.routing_decision.model_used if result.routing_decision else None,
        "model_reason": result.routing_decision.reason if result.routing_decision else None,
        "sources": result.retrieved_sources,
        "response": result.final_response,
        "validation_passed": result.validation.passed if result.validation else None,
        "validation_issues": result.validation.issues if result.validation else [],
        "action_taken": result.action_taken,
    }


@app.post("/analyze-document")
async def analyze_document(file: UploadFile = File(...)):
    """Document Analysis: upload a sustainability/ESG document, get it ingested + analyzed."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    chunks = ingest_file(tmp_path)
    for c in chunks:
        c.source = file.filename
    upserted_count = upsert_chunks(chunks)

    analysis_request = f"Provide a basic sustainability analysis summary of the document: {file.filename}"
    result = handle_request(analysis_request, has_uploaded_document=True)
    log_id = log_request(result)

    return {
        "log_id": log_id,
        "filename": file.filename,
        "chunks_ingested": upserted_count,
        "analysis": result.final_response,
        "model_used": result.routing_decision.model_used if result.routing_decision else None,
        "validation_passed": result.validation.passed if result.validation else None,
    }


@app.get("/regulatory-radar/run")
def regulatory_radar_run():
    """Regulatory Monitoring: run the full ingest->filter->tag->analyze->alert pipeline."""
    results = run_regulatory_radar()
    return {
        "total_ingested": len(results),
        "relevant_count": sum(1 for r in results if r.is_relevant),
        "alerts": [
            {
                "title": r.title,
                "is_relevant": r.is_relevant,
                "matched_keywords": r.matched_keywords,
                "impact_analysis": r.impact_analysis,
                "alert_summary": r.alert_summary,
                "linkedin_post": r.linkedin_post,
            }
            for r in results
        ],
    }


@app.get("/dashboard/requests")
def dashboard_requests(limit: int = 50):
    """Review Interface data feed: recent requests with full decision trail."""
    rows = get_recent_requests(limit=limit)
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "request_text": r.request_text,
            "in_scope": r.in_scope,
            "matched_keywords": r.matched_keywords,
            "scope_reason": r.scope_reason,
            "request_type": r.request_type,
            "model_used": r.model_used,
            "routing_reason": r.routing_reason,
            "retrieved_sources": r.retrieved_sources,
            "final_response": r.final_response,
            "action_taken": r.action_taken,
            "validation_passed": r.validation_passed,
            "validation_issues": r.validation_issues,
        }
        for r in rows
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=settings.PORT, reload=True)
