"""
scope_classifier.py
Determines whether an incoming request is within the "environment & sustainability" scope.

Two-stage check (per assignment requirement: "keywords, topics, categories, or rules"):
  1. Fast keyword/topic match against keywords.json (cheap, deterministic, explainable)
  2. If keyword match is weak/ambiguous, fall back to the fast LLM (Groq) for a judgment call

Returns a structured result the orchestrator can log and show on the review dashboard.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

KEYWORDS_PATH = Path(__file__).parent / "data" / "keywords.json"

with open(KEYWORDS_PATH, "r") as f:
    _KEYWORD_DATA = json.load(f)

ALL_KEYWORDS: list[str] = _KEYWORD_DATA["all_keywords_flat"]
CATEGORIES: dict[str, list[str]] = _KEYWORD_DATA["categories"]

# Minimum number of matched keywords for a confident in-scope decision via keyword match alone.
KEYWORD_CONFIDENCE_THRESHOLD = 1


@dataclass
class ScopeResult:
    in_scope: bool
    method: str                     # "keyword_match" or "llm_fallback"
    matched_keywords: list[str] = field(default_factory=list)
    matched_categories: list[str] = field(default_factory=list)
    confidence: str = "low"         # "high", "medium", "low"
    reason: str = ""


def _find_matched_keywords(text: str) -> list[str]:
    """Case-insensitive substring match of known keywords against the request text."""
    text_lower = text.lower()
    matches = []
    for kw in ALL_KEYWORDS:
        # word-boundary-ish match to avoid partial-word false positives (e.g. "esg" inside another word)
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(kw.lower()) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, text_lower):
            matches.append(kw)
    return matches


def _find_matched_categories(matched_keywords: list[str]) -> list[str]:
    matched_lower = {k.lower() for k in matched_keywords}
    hit_categories = []
    for cat, kws in CATEGORIES.items():
        cat_kws_lower = {k.lower() for k in kws}
        if matched_lower & cat_kws_lower:
            hit_categories.append(cat)
    return hit_categories


def classify_scope(request_text: str) -> ScopeResult:
    """
    Stage 1: keyword/topic matching.
    Returns a ScopeResult. If no keywords match, in_scope=False with method="keyword_match"
    and confidence="low" — the orchestrator decides whether to escalate to the LLM fallback
    (see llm_scope_fallback below) for ambiguous cases.
    """
    matched_keywords = _find_matched_keywords(request_text)
    matched_categories = _find_matched_categories(matched_keywords)

    if len(matched_keywords) >= KEYWORD_CONFIDENCE_THRESHOLD:
        return ScopeResult(
            in_scope=True,
            method="keyword_match",
            matched_keywords=matched_keywords,
            matched_categories=matched_categories,
            confidence="high" if len(matched_keywords) >= 3 else "medium",
            reason=(
                f"Matched {len(matched_keywords)} sustainability keyword(s) "
                f"across {len(matched_categories)} categor(y/ies): "
                f"{', '.join(matched_keywords[:5])}"
                + ("..." if len(matched_keywords) > 5 else "")
            ),
        )

    return ScopeResult(
        in_scope=False,
        method="keyword_match",
        matched_keywords=[],
        matched_categories=[],
        confidence="low",
        reason="No sustainability/environment keywords detected in the request.",
    )


def llm_scope_fallback(request_text: str, groq_client) -> ScopeResult:
    """
    Stage 2: used only when keyword matching is inconclusive (e.g. a request that discusses
    sustainability using synonyms/phrasing not in our keyword list, like "how do I cut my
    factory's electricity bill" — no exact keyword, but arguably energy-related).

    groq_client: an initialized client from models/groq_client.py, passed in so this module
    stays testable without needing network access.
    """
    prompt = (
        "You are a strict scope classifier for a corporate sustainability/ESG AI platform. "
        "Decide if the following user request is about environment, sustainability, ESG, "
        "climate, energy, emissions, or corporate sustainability compliance. "
        "Reply with exactly one word: YES or NO.\n\n"
        f"Request: {request_text}"
    )
    response = groq_client.fast_completion(prompt).strip().upper()
    in_scope = response.startswith("YES")

    return ScopeResult(
        in_scope=in_scope,
        method="llm_fallback",
        matched_keywords=[],
        matched_categories=[],
        confidence="medium",
        reason=f"No direct keyword match; fast LLM judged this as {'in-scope' if in_scope else 'out-of-scope'}.",
    )
