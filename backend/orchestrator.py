"""
orchestrator.py
The ZenAI Orchestrator — the "brain" described in the assignment's Core Architecture (section 4).

Flow per assignment spec:
  1. Receive request
  2. Classify + detect keywords/topics
  3. Check environment & sustainability scope
  4. Apply boundary rules -> reject/redirect/clarify if out-of-scope
  5. Select model(s)
  6. Execute workflow (RAG + model call)
  7. Pass result through Rules Engine
  8. Return final response with full scope/validation trail

NOTE: retriever.py (RAG) is referenced here but built in the next step —
      this module is written against its expected interface so both can be
      developed/tested independently.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from scope_classifier import classify_scope, llm_scope_fallback, ScopeResult
from model_router import classify_request_type, route, RoutingDecision
from rules_engine import validate_response, ValidationResult
from models.groq_client import groq_client

try:
    from retriever import retrieve_relevant_chunks
except ImportError:
    # retriever.py not built yet — safe fallback so orchestrator is testable in isolation.
    def retrieve_relevant_chunks(query: str, top_k: int = 3):
        return []


OUT_OF_SCOPE_MESSAGE = (
    "This request appears to be outside ZenAI's environment & sustainability scope. "
    "ZenAI only handles questions related to ESG, climate, emissions, energy, waste, "
    "biodiversity, water, or corporate sustainability compliance. "
    "Please rephrase your request within that scope, or contact general support for other topics."
)


@dataclass
class ZenAIResponse:
    request_text: str
    timestamp: str
    scope_result: ScopeResult
    request_type: str = ""
    routing_decision: RoutingDecision = None
    retrieved_sources: list = field(default_factory=list)
    final_response: str = ""
    validation: ValidationResult = None
    action_taken: str = ""   # "answered", "rejected", "clarification_requested"


def handle_request(request_text: str, has_uploaded_document: bool = False) -> ZenAIResponse:
    timestamp = datetime.now(timezone.utc).isoformat()

    # Step 1-2: Scope + keyword detection (Stage 1: fast keyword match)
    scope_result = classify_scope(request_text)

    # Escalate to LLM fallback only when keyword match was inconclusive (low confidence).
    if scope_result.confidence == "low":
        scope_result = llm_scope_fallback(request_text, groq_client)

    # Step 3-4: Boundary enforcement — reject out-of-scope requests immediately.
    if not scope_result.in_scope:
        return ZenAIResponse(
            request_text=request_text,
            timestamp=timestamp,
            scope_result=scope_result,
            final_response=OUT_OF_SCOPE_MESSAGE,
            action_taken="rejected",
        )

    # Step 5: Classify request type + route to model(s)
    request_type = classify_request_type(request_text, has_uploaded_document)
    routing_decision = route(request_type)

    # Step 6: Execute workflow — RAG retrieval + model call
    retrieved_chunks = retrieve_relevant_chunks(request_text, top_k=3)
    sources = [chunk.get("source", "unknown") for chunk in retrieved_chunks]
    context_text = "\n\n".join(chunk.get("text", "") for chunk in retrieved_chunks)

    system_prompt = (
        "You are ZenAI, a sustainability/ESG assistant. Answer using ONLY the provided "
        "context where relevant, and cite sources by name. If the context doesn't contain "
        "the answer, say so clearly rather than guessing."
    )
    prompt = f"Context:\n{context_text}\n\nQuestion: {request_text}"

    if "reasoning" in routing_decision.model_used:
        model_response = groq_client.reasoning_completion(prompt, system=system_prompt)
    else:
        model_response = groq_client.fast_completion(prompt, system=system_prompt)

    # Step 7: Validate output against rules
    validation = validate_response(
        response_text=model_response,
        retrieved_sources=sources,
        original_request_in_scope=scope_result.in_scope,
    )

    return ZenAIResponse(
        request_text=request_text,
        timestamp=timestamp,
        scope_result=scope_result,
        request_type=request_type.value,
        routing_decision=routing_decision,
        retrieved_sources=sources,
        final_response=model_response,
        validation=validation,
        action_taken="answered" if validation.passed else "flagged_for_review",
    )
