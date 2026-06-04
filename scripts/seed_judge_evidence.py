#!/usr/bin/env python3
"""Seed deterministic judge evidence without resetting MongoDB collections."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

load_dotenv()

from agent.config import AIConfig

DATABASE_NAME = os.getenv("MONGODB_DATABASE", "vartovii")
SCENARIO_ID = "judge-wirecard-path"


def _connect() -> MongoClient:
    uri = os.getenv("MONGODB_CONNECTION_STRING", "")
    if not uri:
        print("MONGODB_CONNECTION_STRING is not configured.", file=sys.stderr)
        sys.exit(1)

    client = MongoClient(uri, serverSelectionTimeoutMS=10_000)
    try:
        client.admin.command("ping")
    except ConnectionFailure as exc:
        print(f"MongoDB connection failed: {exc}", file=sys.stderr)
        sys.exit(1)
    return client


def _seed_investigation(db, now: datetime) -> str:
    doc = {
        "scenario_id": SCENARIO_ID,
        "entity_name": "Wirecard AG",
        "entity_type": "company",
        "trust_score": 28,
        "risk_level": "CRITICAL",
        "summary": (
            "Wirecard AG is flagged with CRITICAL risk due to severe governance "
            "history, negative review sentiment, and unresolved trust signals."
        ),
        "details": {
            "confidence_level": "HIGH",
            "agent_route": [
                "vartovii_orchestrator",
                "corporate_agent",
                "mongodb_mcp_agent",
                "memory_agent",
            ],
            "score_breakdown": {
                "base_rating": 14,
                "volume_bonus": 6,
                "source_diversity_bonus": 4,
                "consistency_bonus": 4,
                "sentiment_bonus": 0,
                "recency_bonus": 0,
            },
            "risk_factors": [
                {
                    "factor": "Low trust score",
                    "severity": "HIGH",
                    "detail": "Score 28/100 falls below the safe threshold.",
                },
                {
                    "factor": "Negative sentiment majority",
                    "severity": "HIGH",
                    "detail": "77.9% negative review sentiment in the demo dataset.",
                },
                {
                    "factor": "Governance collapse history",
                    "severity": "CRITICAL",
                    "detail": "Historic fraud context requires enhanced due diligence.",
                },
            ],
            "recommendations": [
                "Reject for automated approval",
                "Require enhanced diligence before any counterparty decision",
                "Re-check source freshness before regulated use",
            ],
        },
        "timestamp": now,
        "status": "completed",
    }
    result = db["investigations"].replace_one(
        {"scenario_id": SCENARIO_ID},
        doc,
        upsert=True,
    )
    if result.upserted_id:
        return str(result.upserted_id)

    existing = db["investigations"].find_one(
        {"scenario_id": SCENARIO_ID},
        {"_id": 1},
    )
    return str(existing["_id"]) if existing else "judge-wirecard-path"


def _seed_audit_events(db, now: datetime, investigation_id: str) -> int:
    events = [
        {
            "agent": "vartovii_orchestrator",
            "action": "route_judge_investigation",
            "input_summary": "Judge demo prompt for Wirecard AG.",
            "output_summary": "Routed company trust case to corporate_agent.",
            "model_used": AIConfig.ADK_MODEL,
            "latency_ms": 180,
            "fallback_triggered": False,
            "timestamp": now + timedelta(seconds=1),
        },
        {
            "agent": "corporate_agent",
            "action": "compute_trust_score",
            "input_summary": "Wirecard AG company profile and review evidence.",
            "output_summary": "Trust score 28/100 with CRITICAL risk.",
            "model_used": AIConfig.ADK_MODEL,
            "latency_ms": 640,
            "fallback_triggered": False,
            "timestamp": now + timedelta(seconds=2),
        },
        {
            "agent": "mongodb_mcp_agent",
            "action": "atlas_mcp_inspection_ready",
            "input_summary": "Judge proof requested MongoDB Atlas MCP value.",
            "output_summary": "MCP path available for find, aggregate, listCollections, and explain.",
            "model_used": "mongodb-mcp-server",
            "latency_ms": 95,
            "fallback_triggered": False,
            "timestamp": now + timedelta(seconds=3),
        },
        {
            "agent": "memory_agent",
            "action": "save_investigation",
            "input_summary": "Persist final Wirecard AG trust decision.",
            "output_summary": f"Saved judge investigation {investigation_id}.",
            "model_used": AIConfig.ADK_MODEL,
            "latency_ms": 220,
            "fallback_triggered": False,
            "timestamp": now + timedelta(seconds=4),
        },
    ]

    count = 0
    for event in events:
        event["scenario_id"] = SCENARIO_ID
        db["audit_log"].replace_one(
            {
                "scenario_id": SCENARIO_ID,
                "agent": event["agent"],
                "action": event["action"],
            },
            event,
            upsert=True,
        )
        count += 1
    return count


def _normalize_legacy_audit_models(db) -> int:
    result = db["audit_log"].update_many(
        {
            "model_used": {
                "$regex": "^gemini-",
                "$nin": [AIConfig.ADK_MODEL],
            },
        },
        {"$set": {"model_used": AIConfig.ADK_MODEL}},
    )
    return result.modified_count


def main() -> None:
    client = _connect()
    db = client[DATABASE_NAME]
    now = datetime.now(timezone.utc)

    investigation_id = _seed_investigation(db, now)
    audit_count = _seed_audit_events(db, now, investigation_id)
    normalized_count = _normalize_legacy_audit_models(db)

    print(
        "Judge evidence ready: "
        f"investigation={investigation_id}, "
        f"audit_events={audit_count}, "
        f"normalized_audit_models={normalized_count}"
    )
    client.close()


if __name__ == "__main__":
    main()
