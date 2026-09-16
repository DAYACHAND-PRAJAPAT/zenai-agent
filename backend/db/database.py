"""
db/database.py
Sets up the SQLAlchemy engine/session for the Supabase Postgres database,
and provides helper functions to log requests and alerts.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings
from db.schema import Base, RequestLog, RegulatoryAlert

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL is not set. Add it to your .env file.")
        _engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    return _engine


def get_session():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal()


def init_db():
    """Creates all tables if they don't already exist. Call once at app startup."""
    Base.metadata.create_all(bind=get_engine())


def log_request(zenai_response) -> int:
    """Persists a ZenAIResponse (from orchestrator.py) as a RequestLog row.
    Returns the new row's ID."""
    session = get_session()
    try:
        validation = zenai_response.validation
        scope = zenai_response.scope_result
        routing = zenai_response.routing_decision

        row = RequestLog(
            request_text=zenai_response.request_text,
            in_scope=scope.in_scope,
            scope_method=scope.method,
            matched_keywords=scope.matched_keywords,
            matched_categories=scope.matched_categories,
            scope_confidence=scope.confidence,
            scope_reason=scope.reason,
            request_type=zenai_response.request_type,
            model_used=routing.model_used if routing else None,
            routing_reason=routing.reason if routing else None,
            retrieved_sources=zenai_response.retrieved_sources,
            final_response=zenai_response.final_response,
            action_taken=zenai_response.action_taken,
            validation_passed=validation.passed if validation else None,
            validation_checks=validation.checks if validation else None,
            validation_issues=validation.issues if validation else None,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.id
    finally:
        session.close()


def log_regulatory_alert(alert_data: dict) -> int:
    session = get_session()
    try:
        row = RegulatoryAlert(**alert_data)
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.id
    finally:
        session.close()


def get_recent_requests(limit: int = 50) -> list[RequestLog]:
    session = get_session()
    try:
        return (
            session.query(RequestLog)
            .order_by(RequestLog.timestamp.desc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()
