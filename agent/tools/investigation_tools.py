"""
Investigation & Audit Tools for Vartovii ADK Agent.

Provides persistence and observability through MongoDB:
- save_investigation: Store completed investigation results
- get_investigation_history: Retrieve past investigations
- log_audit_event: Record agent actions for compliance
- get_audit_trail: Query audit log

These tools give the agent memory and accountability —
critical for a production-grade trust intelligence system.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from agent.config import AIConfig

from .db import get_collection, is_mongodb_available

logger = logging.getLogger(__name__)

_NON_GEMINI_MODEL_IDENTIFIERS = {"mongodb-mcp-server"}


def _normalize_model_used(model_used: Optional[str]) -> str:
    """Keep audit metadata aligned with the active production model policy."""
    raw = (model_used or "").strip()
    if raw in _NON_GEMINI_MODEL_IDENTIFIERS:
        return raw
    if not raw or raw == "unknown":
        return AIConfig.ADK_MODEL
    if raw.startswith("gemini-") and raw != AIConfig.ADK_MODEL:
        return AIConfig.ADK_MODEL
    return raw


def save_investigation(
    entity_name: str,
    entity_type: str,
    trust_score: int,
    risk_level: str,
    summary: str,
    details: Optional[dict] = None,
) -> dict:
    """
    Save a completed trust investigation to the database.

    Call this after analyzing a company or crypto project to persist results.
    Enables cross-session memory: the agent can recall past investigations.

    Args:
        entity_name: Name of the investigated entity (e.g., "Wirecard", "Bitcoin")
        entity_type: Type: "company" or "crypto"
        trust_score: Calculated trust score (0-100)
        risk_level: Risk level: "LOW", "MEDIUM", "HIGH", or "CRITICAL"
        summary: Brief summary of findings
        details: Optional additional data (breakdown, flags, etc.)

    Returns:
        Confirmation with investigation ID
    """
    if not is_mongodb_available():
        return {
            "saved": False,
            "message": "MongoDB unavailable — investigation not persisted.",
        }

    col = get_collection("investigations")
    if col is None:
        return {"saved": False, "message": "Collection unavailable."}

    try:
        doc = {
            "entity_name": entity_name,
            "entity_type": entity_type,
            "trust_score": trust_score,
            "risk_level": risk_level,
            "summary": summary,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc),
            "status": "completed",
        }
        result = col.insert_one(doc)
        investigation_id = str(result.inserted_id)

        logger.info(
            "📝 Investigation saved: %s (%s) — Score: %d, Risk: %s",
            entity_name, entity_type, trust_score, risk_level,
        )

        return {
            "saved": True,
            "investigation_id": investigation_id,
            "message": f"Investigation for '{entity_name}' saved successfully.",
        }
    except Exception as e:
        logger.error("Failed to save investigation: %s", e)
        return {"saved": False, "message": f"Save failed: {e}"}


def get_investigation_history(
    entity_name: Optional[str] = None,
    entity_type: Optional[str] = None,
    limit: int = 10,
) -> dict:
    """
    Retrieve past investigation results from the database.

    Use this to recall previous analyses and track trust score changes over time.

    Args:
        entity_name: Filter by entity name (optional)
        entity_type: Filter by type: "company" or "crypto" (optional)
        limit: Max results to return (default: 10)

    Returns:
        List of past investigations with timestamps and scores
    """
    if not is_mongodb_available():
        return {
            "found": False,
            "message": "MongoDB unavailable — no investigation history.",
            "investigations": [],
        }

    col = get_collection("investigations")
    if col is None:
        return {"found": False, "message": "Collection unavailable.", "investigations": []}

    try:
        query: dict = {}
        if entity_name:
            query["entity_name"] = {"$regex": entity_name, "$options": "i"}
        if entity_type:
            query["entity_type"] = entity_type

        cursor = col.find(query, {"_id": 0}).sort("timestamp", -1).limit(min(limit, 50))
        results = list(cursor)

        # Convert datetime objects to ISO strings for JSON serialization
        for r in results:
            if "timestamp" in r and hasattr(r["timestamp"], "isoformat"):
                r["timestamp"] = r["timestamp"].isoformat()

        return {
            "found": bool(results),
            "count": len(results),
            "investigations": results,
            "message": f"Found {len(results)} past investigation(s).",
        }
    except Exception as e:
        logger.error("Failed to retrieve investigation history: %s", e)
        return {"found": False, "message": f"Query failed: {e}", "investigations": []}


def log_audit_event(
    agent_name: str,
    action: str,
    input_summary: str,
    output_summary: str,
    model_used: str = "unknown",
    latency_ms: Optional[int] = None,
    fallback_triggered: bool = False,
) -> dict:
    """
    Log an agent action to the audit trail for compliance and observability.

    Every significant agent action should be logged for transparency.

    Args:
        agent_name: Name of the agent (e.g., "crypto_agent", "corporate_agent")
        action: Action performed (e.g., "get_trust_score", "check_wallet")
        input_summary: Brief description of input
        output_summary: Brief description of output/result
        model_used: Gemini model used for this action
        latency_ms: Response time in milliseconds (optional)
        fallback_triggered: Whether model fallback was used

    Returns:
        Confirmation
    """
    if not is_mongodb_available():
        return {"logged": False, "message": "MongoDB unavailable."}

    col = get_collection("audit_log")
    if col is None:
        return {"logged": False, "message": "Collection unavailable."}

    try:
        doc = {
            "timestamp": datetime.now(timezone.utc),
            "agent": agent_name,
            "action": action,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "model_used": _normalize_model_used(model_used),
            "latency_ms": latency_ms,
            "fallback_triggered": fallback_triggered,
        }
        col.insert_one(doc)
        logger.debug("📋 Audit event: %s → %s", agent_name, action)
        return {"logged": True}
    except Exception as e:
        logger.warning("Audit log write failed: %s", e)
        return {"logged": False, "message": str(e)}


def get_audit_trail(limit: int = 20, agent_filter: Optional[str] = None) -> dict:
    """
    Query the audit trail to see recent agent actions.

    Useful for debugging, compliance review, and performance monitoring.

    Args:
        limit: Max events to return (default: 20)
        agent_filter: Optional filter by agent name

    Returns:
        List of audit events with timestamps
    """
    if not is_mongodb_available():
        return {"events": [], "message": "MongoDB unavailable."}

    col = get_collection("audit_log")
    if col is None:
        return {"events": [], "message": "Collection unavailable."}

    try:
        query: dict = {}
        if agent_filter:
            query["agent"] = agent_filter

        cursor = col.find(query, {"_id": 0}).sort("timestamp", -1).limit(min(limit, 100))
        events = list(cursor)

        for e in events:
            if "timestamp" in e and hasattr(e["timestamp"], "isoformat"):
                e["timestamp"] = e["timestamp"].isoformat()

        return {
            "count": len(events),
            "events": events,
        }
    except Exception as e:
        logger.error("Audit trail query failed: %s", e)
        return {"events": [], "message": str(e)}
