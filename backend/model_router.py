"""
model_router.py
Decides which AI/ML model (or combination) should handle an in-scope request,
and records WHY — the assignment explicitly requires the dashboard to show
"model selected" + "reason for model selection".
"""

from dataclasses import dataclass
from enum import Enum


class RequestType(str, Enum):
    DOCUMENT_ANALYSIS = "document_analysis"
    AI_CHAT = "ai_chat"
    REGULATORY_MONITORING = "regulatory_monitoring"
    ANOMALY_FORECAST = "anomaly_forecast"
    UNKNOWN = "unknown"


@dataclass
class RoutingDecision:
    request_type: RequestType
    model_used: str          # "groq_fast", "groq_reasoning", "ml_model", or a combination
    reason: str


# Keyword hints used to classify request type before routing.
# (Kept simple/deterministic for the prototype; could be replaced by an LLM classifier call.)
_TYPE_HINTS = {
    RequestType.DOCUMENT_ANALYSIS: ["analyze this document", "uploaded document", "review this report", "pdf", "document analysis"],
    RequestType.REGULATORY_MONITORING: ["regulation", "regulatory", "new policy", "compliance update", "csrd", "law", "mandate"],
    RequestType.ANOMALY_FORECAST: ["forecast", "predict", "anomaly", "trend", "projection", "unusual pattern"],
}


def classify_request_type(request_text: str, has_uploaded_document: bool = False) -> RequestType:
    if has_uploaded_document:
        return RequestType.DOCUMENT_ANALYSIS

    text_lower = request_text.lower()
    for req_type, hints in _TYPE_HINTS.items():
        if any(hint in text_lower for hint in hints):
            return req_type

    return RequestType.AI_CHAT  # default: a general sustainability question


def route(request_type: RequestType) -> RoutingDecision:
    """
    Routing logic per assignment's AI Engine spec:
      - Fast LLM (Gemma)  -> classification, extraction, mapping, initial scope detection
      - Claude/reasoning LLM (here: Groq Llama 3.3 70B) -> reasoning, analysis, complex responses, impact assessment
      - ML Model -> anomaly detection / forecasting
    """
    if request_type == RequestType.AI_CHAT:
        return RoutingDecision(
            request_type=request_type,
            model_used="groq_reasoning",
            reason="General sustainability Q&A needs contextual reasoning over retrieved (RAG) sources, "
                   "not just classification — routed to the reasoning model.",
        )

    if request_type == RequestType.DOCUMENT_ANALYSIS:
        return RoutingDecision(
            request_type=request_type,
            model_used="groq_fast+groq_reasoning",
            reason="Fast model extracts/structures key data points from the document first; "
                   "reasoning model then produces the analysis and impact summary.",
        )

    if request_type == RequestType.REGULATORY_MONITORING:
        return RoutingDecision(
            request_type=request_type,
            model_used="groq_fast+groq_reasoning",
            reason="Fast model tags/filters incoming regulatory content by relevance; "
                   "reasoning model analyses potential business/environmental impact and drafts the alert.",
        )

    if request_type == RequestType.ANOMALY_FORECAST:
        return RoutingDecision(
            request_type=request_type,
            model_used="ml_model",
            reason="Numerical anomaly detection/forecasting is a statistical task better suited to a "
                   "dedicated ML model than an LLM.",
        )

    return RoutingDecision(
        request_type=RequestType.UNKNOWN,
        model_used="groq_fast",
        reason="Could not confidently classify request type; using fast model for a lightweight response "
               "and flagging for clarification.",
    )
