"""
db/schema.py
SQLAlchemy models for storing every ZenAI request + its full decision trail.
This IS the data source for the Review Interface/dashboard (assignment section 8).
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class RequestLog(Base):
    """One row per user request, capturing every field the Review Interface must show."""
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Request
    request_text = Column(Text, nullable=False)

    # Scope / boundary check
    in_scope = Column(Boolean, nullable=False)
    scope_method = Column(String)           # "keyword_match" or "llm_fallback"
    matched_keywords = Column(JSON)          # list[str]
    matched_categories = Column(JSON)        # list[str]
    scope_confidence = Column(String)
    scope_reason = Column(Text)

    # Classification + routing
    request_type = Column(String)
    model_used = Column(String)
    routing_reason = Column(Text)

    # RAG
    retrieved_sources = Column(JSON)         # list[str]

    # Output
    final_response = Column(Text)
    action_taken = Column(String)            # "answered" | "rejected" | "flagged_for_review"

    # Validation
    validation_passed = Column(Boolean)
    validation_checks = Column(JSON)         # dict of check_name -> bool
    validation_issues = Column(JSON)         # list[str]


class RegulatoryAlert(Base):
    """One row per generated regulatory radar alert."""
    __tablename__ = "regulatory_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    source_title = Column(String)
    raw_content = Column(Text)
    is_relevant = Column(Boolean)
    matched_keywords = Column(JSON)
    impact_analysis = Column(Text)
    alert_summary = Column(Text)
    linkedin_post = Column(Text)
