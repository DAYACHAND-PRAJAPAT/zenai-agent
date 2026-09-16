"""
regulatory_radar.py
Implements the assignment's Regulatory Radar pipeline exactly as specified:
  Ingest -> Filter -> Apply Boundary Rules -> Tag -> AI Impact Analysis -> Output

For a free prototype, "ingest" reads from mock JSON files (data/mock_regulatory_feed.json)
instead of a live news API — this satisfies the requirement without needing paid API keys.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from scope_classifier import classify_scope
from models.groq_client import groq_client

MOCK_FEED_PATH = Path(__file__).parent / "data" / "mock_regulatory_feed.json"

LINKEDIN_PROMPT_TEMPLATE = """You are a sustainability regulatory expert. A new ESG or climate \
regulation, framework, or policy update has been announced.

Your task:
1. Write a LinkedIn post (180-250 words) breaking down the regulatory development.
2. Structure: What changed -> Who it affects -> Key deadlines or requirements -> What companies should do now.
3. Open with a clear headline line.
4. Use short paragraphs or a brief numbered list (max 4 points) for readability.
5. End with a practical tip or resource recommendation.
6. Add 5-7 relevant hashtags.

Tone: Expert compliance advisor - clear, practical, non-alarmist.

Regulation/policy input: {content}
"""


@dataclass
class RegulatoryItem:
    title: str
    content: str
    is_relevant: bool = False
    matched_keywords: list = field(default_factory=list)
    impact_analysis: str = ""
    alert_summary: str = ""
    linkedin_post: str = ""


def ingest_mock_feed() -> list[dict]:
    """Step 1: Ingest. Reads mock regulatory/news items."""
    if not MOCK_FEED_PATH.exists():
        return []
    with open(MOCK_FEED_PATH, "r") as f:
        return json.load(f)


def filter_and_tag(raw_items: list[dict]) -> list[RegulatoryItem]:
    """Steps 2-4: Filter (keyword/Boolean) -> Apply boundary rules -> Tag relevant items."""
    tagged_items = []
    for item in raw_items:
        combined_text = f"{item['title']} {item['content']}"
        scope_result = classify_scope(combined_text)

        tagged_items.append(RegulatoryItem(
            title=item["title"],
            content=item["content"],
            is_relevant=scope_result.in_scope,
            matched_keywords=scope_result.matched_keywords,
        ))
    return tagged_items


def analyze_impact(item: RegulatoryItem) -> RegulatoryItem:
    """Step 5: AI Impact Analysis. Only runs on relevant (in-scope) items."""
    if not item.is_relevant:
        return item

    prompt = (
        f"A new regulatory/sustainability update has been detected:\n\n"
        f"Title: {item.title}\nContent: {item.content}\n\n"
        f"Analyze its potential business, environmental, or sustainability impact "
        f"in 3-4 concise sentences."
    )
    item.impact_analysis = groq_client.reasoning_completion(prompt)
    return item


def generate_alert(item: RegulatoryItem) -> RegulatoryItem:
    """Step 6: Generate a structured alert summary."""
    if not item.is_relevant:
        return item

    item.alert_summary = (
        f"ALERT: {item.title}\n"
        f"Matched topics: {', '.join(item.matched_keywords[:5])}\n"
        f"Impact: {item.impact_analysis}"
    )
    return item


def generate_linkedin_post(item: RegulatoryItem) -> RegulatoryItem:
    """Step 7 (assignment section 6): Generate a LinkedIn-style post using the supplied prompt."""
    if not item.is_relevant:
        return item

    prompt = LINKEDIN_PROMPT_TEMPLATE.format(content=f"{item.title}. {item.content}")
    item.linkedin_post = groq_client.reasoning_completion(prompt)
    return item


def run_regulatory_radar() -> list[RegulatoryItem]:
    """Runs the full pipeline: Ingest -> Filter -> Tag -> Impact Analysis -> Output."""
    raw_items = ingest_mock_feed()
    tagged_items = filter_and_tag(raw_items)

    results = []
    for item in tagged_items:
        item = analyze_impact(item)
        item = generate_alert(item)
        item = generate_linkedin_post(item)
        results.append(item)

    return results
