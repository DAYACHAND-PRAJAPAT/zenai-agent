"""
rules_engine.py
Validates AI-generated responses before they're returned to the user.
Per assignment: "Prevent unsupported, inconsistent, or out-of-scope responses."

This runs AFTER the model generates a response and AFTER RAG retrieval,
as the final checkpoint before the orchestrator returns anything.
"""

from dataclasses import dataclass, field
from scope_classifier import classify_scope


@dataclass
class ValidationResult:
    passed: bool
    checks: dict = field(default_factory=dict)   # individual check name -> pass/fail
    issues: list = field(default_factory=list)    # human-readable list of problems found


def validate_response(
    response_text: str,
    retrieved_sources: list[str],
    original_request_in_scope: bool,
) -> ValidationResult:
    """
    Runs a sequence of rule checks on a generated response.
    Each check is independent and explainable — this list is exactly what
    the review dashboard's "Validation status" field should display.
    """
    checks = {}
    issues = []

    # Rule 1: Scope consistency — a response must not drift out of the sustainability
    # scope even if the original request was in-scope.
    response_scope = classify_scope(response_text)
    single_word_hit = any(
        word in response_text.lower()
        for word in ["scope", "emission", "sustainab", "esg", "carbon", "climate", "energy"]
    )
    stays_in_scope = response_scope.in_scope or single_word_hit
    checks["response_stays_in_scope"] = stays_in_scope
    if not stays_in_scope:
        issues.append(
            "Generated response does not contain sustainability-related content, "
            "even though the request was classified in-scope."
        )

    # Rule 2: Original request must have been in-scope to begin with.
    checks["request_was_in_scope"] = original_request_in_scope
    if not original_request_in_scope:
        issues.append("Request was out-of-scope; response should not have been generated.")

    # Rule 3: Citation requirement — RAG-backed answers must have at least one source,
    # unless the response explicitly says information wasn't found.
    no_info_phrases = ["couldn't find", "no relevant information", "not available in the knowledge base"]
    claims_no_info = any(p in response_text.lower() for p in no_info_phrases)
    has_sources = len(retrieved_sources) > 0
    checks["has_citations_or_admits_gap"] = has_sources or claims_no_info
    if not has_sources and not claims_no_info:
        issues.append("Response makes claims without any retrieved source citations.")

    # Rule 4: Minimum response quality — not empty, not a bare error string.
    checks["non_empty_response"] = bool(response_text and len(response_text.strip()) > 10)
    if not checks["non_empty_response"]:
        issues.append("Response is empty or too short to be meaningful.")

    all_passed = all(checks.values())

    return ValidationResult(passed=all_passed, checks=checks, issues=issues)
