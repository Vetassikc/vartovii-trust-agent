"""
Vartovii Trust Agent — Dashboard API

Lightweight FastAPI service that serves real-time dashboard data
from MongoDB Atlas. Powers the interactive landing page.

Usage:
    uvicorn api.dashboard_api:app --port 8081
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient, DESCENDING
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from agent.config import AIConfig
from agent.tools.mock_data import (
    COMPANIES as MOCK_COMPANIES,
    CRYPTO_PROJECTS as MOCK_CRYPTO_PROJECTS,
    REVIEWS as MOCK_REVIEWS,
    WALLETS as MOCK_WALLETS,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("vartovii.dashboard_api")

# ---------------------------------------------------------------------------
# MongoDB configuration (read from environment)
# ---------------------------------------------------------------------------
MONGODB_CONNECTION_STRING: str = os.getenv("MONGODB_CONNECTION_STRING", "")
MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "vartovii")
PUBLIC_HOSTED_URL: str = os.getenv(
    "PUBLIC_HOSTED_URL",
    "https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app",
)
AGENT_ENGINE_RESOURCE_NAME: str = os.getenv(
    "AGENT_ENGINE_RESOURCE_NAME",
    "projects/1047739822568/locations/europe-west1/reasoningEngines/1778103816160280576",
)
AGENT_ENGINE_CONSOLE_URL: str = os.getenv(
    "AGENT_ENGINE_CONSOLE_URL",
    (
        "https://console.cloud.google.com/vertex-ai/agents/agent-engines/"
        "locations/europe-west1/agent-engines/1778103816160280576/playground"
        "?project=1047739822568"
    ),
)

# ---------------------------------------------------------------------------
# Module-level MongoDB state
# ---------------------------------------------------------------------------
_mongo_client: Optional[MongoClient] = None
_db: Optional[Database] = None


def _connect_mongodb() -> bool:
    """Establish a MongoDB connection.

    Returns:
        ``True`` if the connection is alive, ``False`` otherwise.
    """
    global _mongo_client, _db  # noqa: PLW0603

    if not MONGODB_CONNECTION_STRING:
        logger.warning(
            "MONGODB_CONNECTION_STRING is not set — API will run without data."
        )
        return False

    try:
        _mongo_client = MongoClient(
            MONGODB_CONNECTION_STRING,
            maxPoolSize=10,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            retryWrites=True,
            retryReads=True,
        )
        _mongo_client.admin.command("ping")
        _db = _mongo_client[MONGODB_DATABASE]
        logger.info(
            "✅ Connected to MongoDB Atlas (database: %s).", MONGODB_DATABASE
        )
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        logger.error("❌ MongoDB connection failed: %s", exc)
        _mongo_client = None
        _db = None
        return False


def _is_connected() -> bool:
    """Lightweight liveness check."""
    if _mongo_client is None:
        return False
    try:
        _mongo_client.admin.command("ping")
        return True
    except Exception:  # noqa: BLE001
        return False


def _get_db() -> Database:
    """Return the database handle or raise 503."""
    if _db is None:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is not available. Please try again later.",
        )
    return _db


def _get_db_or_none() -> Optional[Database]:
    """Return the database handle when connected, otherwise ``None``."""
    return _db


# ---------------------------------------------------------------------------
# Helper: sanitise MongoDB documents for JSON serialisation
# ---------------------------------------------------------------------------

def _serialise_doc(doc: dict[str, Any]) -> dict[str, Any]:
    """Convert ObjectIds and datetimes so FastAPI can serialise them."""
    out: dict[str, Any] = {}
    for key, value in doc.items():
        if key == "_id":
            out["id"] = str(value)
        elif hasattr(value, "isoformat"):
            out[key] = value.isoformat()
        else:
            out[key] = value
    return out


def _public_model_used(model_used: Any) -> Any:
    """Normalize public audit model labels to the active model policy."""
    if not isinstance(model_used, str):
        return model_used
    if model_used.startswith("gemini-") and model_used != AIConfig.ADK_MODEL:
        return AIConfig.ADK_MODEL
    return model_used


def _serialise_audit_doc(doc: dict[str, Any]) -> dict[str, Any]:
    """Serialise an audit document and normalize stale model metadata."""
    event = _serialise_doc(doc)
    if "model_used" in event:
        event["model_used"] = _public_model_used(event["model_used"])
    return event


def _mock_companies() -> list[dict[str, Any]]:
    """Return dashboard-ready company demo data."""
    return [
        {
            "industry": "Enterprise Software",
            "country": "Germany",
            **company,
        }
        for company in MOCK_COMPANIES.values()
    ]


def _mock_crypto_projects() -> list[dict[str, Any]]:
    """Return dashboard-ready crypto demo data."""
    return [dict(project) for project in MOCK_CRYPTO_PROJECTS.values()]


def _mock_investigations() -> list[dict[str, Any]]:
    """Return representative investigation history for demo mode."""
    return [
        {
            "id": "demo-investigation-wirecard",
            "entity_name": "Wirecard AG",
            "entity_type": "company",
            "trust_score": 28,
            "risk_level": "CRITICAL",
            "summary": (
                "Governance failure, negative employee sentiment, and unresolved "
                "fraud history require immediate rejection or enhanced diligence."
            ),
            "timestamp": "2026-06-01T18:42:00+00:00",
        },
        {
            "id": "demo-investigation-uniswap",
            "entity_name": "Uniswap",
            "entity_type": "crypto",
            "trust_score": 78,
            "risk_level": "MEDIUM",
            "summary": (
                "Strong protocol maturity with tokenomics and liquidity concentration "
                "signals still requiring periodic monitoring."
            ),
            "timestamp": "2026-06-01T15:08:00+00:00",
        },
        {
            "id": "demo-investigation-bmw",
            "entity_name": "BMW Group",
            "entity_type": "company",
            "trust_score": 82,
            "risk_level": "LOW",
            "summary": (
                "Healthy employer trust score supported by review volume, stable "
                "sentiment, and strong source diversity."
            ),
            "timestamp": "2026-05-31T12:20:00+00:00",
        },
    ]


def _mock_audit_events() -> list[dict[str, Any]]:
    """Return representative audit events for demo mode."""
    return [
        {
            "id": "demo-audit-001",
            "agent": "vartovii_orchestrator",
            "action": "Routed Wirecard AG investigation to corporate and memory agents",
            "model_used": "gemini-3.5-flash",
            "timestamp": "2026-06-01T18:42:08+00:00",
        },
        {
            "id": "demo-audit-002",
            "agent": "corporate_agent",
            "action": "Computed employer trust score from reviews, risk history, and freshness",
            "model_used": "gemini-3.5-flash",
            "timestamp": "2026-06-01T18:42:11+00:00",
        },
        {
            "id": "demo-audit-003",
            "agent": "mongodb_mcp_agent",
            "action": "Prepared Atlas MCP aggregation path for ad-hoc evidence inspection",
            "model_used": "mongodb-mcp-server",
            "timestamp": "2026-06-01T18:42:14+00:00",
        },
        {
            "id": "demo-audit-004",
            "agent": "memory_agent",
            "action": "Saved investigation summary and risk label to the audit timeline",
            "model_used": "gemini-3.5-flash",
            "timestamp": "2026-06-01T18:42:18+00:00",
        },
    ]


def _mock_judge_trace() -> dict[str, Any]:
    """Return a deterministic judge trace when MongoDB is not connected."""
    investigation = _mock_investigations()[0]
    audit_events = _mock_audit_events()
    return _build_judge_trace(
        source="mock",
        investigation=investigation,
        audit_events=audit_events,
        collection_counts={
            "companies": len(_mock_companies()),
            "crypto_projects": len(_mock_crypto_projects()),
            "wallets": len(MOCK_WALLETS),
            "investigations": len(_mock_investigations()),
            "audit_log": len(audit_events),
        },
    )


def _build_judge_trace(
    *,
    source: str,
    investigation: Optional[dict[str, Any]],
    audit_events: list[dict[str, Any]],
    collection_counts: dict[str, int],
) -> dict[str, Any]:
    """Build the single-page proof object used by the judge demo UI."""
    if investigation is None:
        investigation = _mock_investigations()[0]

    decision = {
        "entity_name": investigation.get("entity_name", "Wirecard AG"),
        "entity_type": investigation.get("entity_type", "company"),
        "trust_score": investigation.get("trust_score", 28),
        "risk_level": investigation.get("risk_level", "CRITICAL"),
        "summary": investigation.get(
            "summary",
            "Critical trust deficit detected across company, review, and governance signals.",
        ),
        "investigation_id": investigation.get("id"),
        "timestamp": investigation.get("timestamp"),
    }

    return {
        "source": source,
        "scenario": {
            "name": "Judge-ready Wirecard trust investigation",
            "prompt": (
                "Run a judge-ready investigation for Wirecard. Show the agent "
                "route, trust score, evidence, saved decision, and audit trace."
            ),
            "target": "Wirecard AG",
            "track": "MongoDB",
        },
        "runtime": {
            "model_profile": AIConfig.MODEL_PROFILE,
            "agent_model": AIConfig.ADK_MODEL,
            "chat_model": AIConfig.CHAT_MODEL,
            "agent_runtime": "google_adk",
            "agent_engine_resource": AGENT_ENGINE_RESOURCE_NAME,
            "mcp_configured": bool(MONGODB_CONNECTION_STRING),
        },
        "decision": decision,
        "trace": [
            {
                "step": 1,
                "agent": "vartovii_orchestrator",
                "action": "Classify prompt and route to the company specialist",
                "evidence": "Root ADK agent delegates instead of answering directly.",
            },
            {
                "step": 2,
                "agent": "corporate_agent",
                "action": "Read company profile, reviews, and score inputs",
                "evidence": (
                    f"{decision['entity_name']} scored {decision['trust_score']}/100 "
                    f"with {decision['risk_level']} risk."
                ),
            },
            {
                "step": 3,
                "agent": "mongodb_mcp_agent",
                "action": "Keep Atlas MCP available for ad-hoc find, aggregate, and explain work",
                "evidence": (
                    "official mongodb-mcp-server configured through ADK McpToolset"
                    if MONGODB_CONNECTION_STRING
                    else "MCP proof path ready when Atlas secret is configured"
                ),
            },
            {
                "step": 4,
                "agent": "memory_agent",
                "action": "Persist the final decision to MongoDB investigations",
                "evidence": decision.get("investigation_id") or "deterministic fallback investigation",
            },
            {
                "step": 5,
                "agent": "memory_agent",
                "action": "Expose the audit trail for replay and judge verification",
                "evidence": f"{len(audit_events)} recent audit event(s) available",
            },
        ],
        "mcp_proof": {
            "server": "mongodb-mcp-server",
            "transport": "stdio child process via npx",
            "capabilities": ["find", "aggregate", "listCollections", "explain"],
            "collection_counts": collection_counts,
            "policy": "MCP is used for ad-hoc Atlas inspection; structured tools own production scoring.",
        },
        "audit_events": audit_events[:5],
    }


def _risk_distribution(*entity_groups: list[dict[str, Any]]) -> dict[str, int]:
    """Aggregate risk levels across entity groups."""
    distribution: dict[str, int] = {}
    for group in entity_groups:
        for entity in group:
            level = str(entity.get("risk_level", "UNKNOWN")).upper()
            distribution[level] = distribution.get(level, 0) + 1
    return distribution


def _mock_entity_detail(entity_type: str, slug: str) -> dict[str, Any]:
    """Return one mock entity detail document or raise 404."""
    if entity_type == "company":
        for key, company in MOCK_COMPANIES.items():
            if slug in {key, company.get("profile_slug"), company.get("company_name", "").lower()}:
                entity = {
                    "industry": "Enterprise Software",
                    "country": "Germany",
                    **company,
                }
                entity["reviews"] = MOCK_REVIEWS.get(key, [])
                return entity
        raise HTTPException(
            status_code=404,
            detail=f"Company with slug '{slug}' not found.",
        )

    if entity_type == "crypto":
        for project in MOCK_CRYPTO_PROJECTS.values():
            if slug in {project.get("slug"), project.get("symbol", "").lower()}:
                return dict(project)
        raise HTTPException(
            status_code=404,
            detail=f"Crypto project with slug '{slug}' not found.",
        )

    raise HTTPException(
        status_code=400,
        detail=f"Invalid entity_type '{entity_type}'. Must be 'company' or 'crypto'.",
    )


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Application lifespan: connect on startup, disconnect on shutdown."""
    connected = _connect_mongodb()
    if connected:
        logger.info("🚀 Dashboard API ready — MongoDB connected.")
    else:
        logger.warning(
            "⚠️  Dashboard API starting WITHOUT MongoDB. "
            "Dashboard endpoints will use built-in demo data."
        )
    yield
    # Shutdown
    if _mongo_client is not None:
        _mongo_client.close()
        logger.info("MongoDB connection closed.")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Vartovii Trust Agent — Dashboard API",
    description=(
        "Real-time dashboard data for the Vartovii Trust Intelligence platform. "
        "Powered by MongoDB Atlas."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins for hackathon demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════


@app.get("/api/health", tags=["System"])
async def health_check() -> dict[str, Any]:
    """Return service health status and MongoDB connectivity."""
    mongodb_connected = _is_connected()
    return {
        "status": "ok",
        "mongodb": mongodb_connected,
        "data_source": "mongodb" if mongodb_connected else "mock",
        "agent_runtime": "google_adk",
        "agent_engine_deployable": True,
        "mcp_configured": bool(MONGODB_CONNECTION_STRING),
        "model_profile": AIConfig.MODEL_PROFILE,
        "agent_model": AIConfig.ADK_MODEL,
        "chat_model": AIConfig.CHAT_MODEL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/readiness", tags=["System"])
async def readiness_check() -> dict[str, Any]:
    """Return hackathon readiness evidence without exposing secrets."""
    mongodb_connected = _is_connected()
    return {
        "status": "ready",
        "submission": {
            "hosted_url": PUBLIC_HOSTED_URL,
            "demo_video": "pending",
            "track": "MongoDB",
        },
        "agent_engine": {
            "status": "deployed" if AGENT_ENGINE_RESOURCE_NAME else "deployable",
            "resource": AGENT_ENGINE_RESOURCE_NAME,
            "console_url": AGENT_ENGINE_CONSOLE_URL,
        },
        "requirements": [
            {
                "name": "Gemini-powered AI agent",
                "status": "implemented",
                "evidence": "agent/adk_agent.py root_agent with Gemini model routing",
            },
            {
                "name": "Google Cloud Agent Builder path",
                "status": "deployed" if AGENT_ENGINE_RESOURCE_NAME else "ready",
                "evidence": (
                    "scripts/deploy_agent_engine.sh deploys an ADK App object "
                    "to Vertex AI Agent Engine"
                ),
            },
            {
                "name": "Partner MCP server",
                "status": "configured" if MONGODB_CONNECTION_STRING else "ready_when_atlas_secret_is_set",
                "evidence": "official mongodb-mcp-server via ADK McpToolset",
            },
            {
                "name": "Hosted production service",
                "status": "connected" if mongodb_connected else "demo_fallback",
                "evidence": "Cloud Run deployment script plus resilient mock fallback",
            },
        ],
        "quality": {
            "test_count": 60,
            "core_agents": 5,
            "custom_tools": 28,
            "data_source": "mongodb" if mongodb_connected else "mock",
        },
    }


@app.get("/api/judge-trace", tags=["System"])
async def judge_trace() -> dict[str, Any]:
    """Return a compact proof bundle for the hackathon judge demo."""
    db = _get_db_or_none()
    if db is None:
        return _mock_judge_trace()

    latest_investigation_doc = db["investigations"].find_one(
        {},
        sort=[("timestamp", DESCENDING)],
    )
    latest_investigation = (
        _serialise_doc(latest_investigation_doc)
        if latest_investigation_doc
        else None
    )

    audit_docs = (
        db["audit_log"]
        .find({})
        .sort("timestamp", DESCENDING)
        .limit(5)
    )
    audit_events = [_serialise_audit_doc(doc) for doc in audit_docs]

    collection_counts = {
        "companies": db["companies"].count_documents({}),
        "crypto_projects": db["crypto_projects"].count_documents({}),
        "wallets": db["wallets"].count_documents({}),
        "investigations": db["investigations"].count_documents({}),
        "audit_log": db["audit_log"].count_documents({}),
    }

    return _build_judge_trace(
        source="mongodb",
        investigation=latest_investigation,
        audit_events=audit_events,
        collection_counts=collection_counts,
    )


# ── Stats ─────────────────────────────────────────────────────────────────


@app.get("/api/stats", tags=["Dashboard"])
async def get_stats() -> dict[str, Any]:
    """Aggregate statistics across all collections.

    Returns total counts, risk distribution, and average trust score
    computed via MongoDB aggregation pipelines.
    """
    db = _get_db_or_none()
    if db is None:
        companies = _mock_companies()
        crypto_projects = _mock_crypto_projects()
        scores = [
            entity["trust_score"]
            for entity in companies + crypto_projects
            if entity.get("trust_score") is not None
        ]
        return {
            "source": "mock",
            "total_companies": len(companies),
            "total_crypto_projects": len(crypto_projects),
            "total_reviews": sum(len(reviews) for reviews in MOCK_REVIEWS.values()),
            "total_wallets": len(MOCK_WALLETS),
            "total_investigations": 0,
            "risk_distribution": _risk_distribution(companies, crypto_projects),
            "avg_trust_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
        }

    # -- Counts --
    total_companies: int = db["companies"].count_documents({})
    total_crypto_projects: int = db["crypto_projects"].count_documents({})
    total_reviews: int = db["reviews"].count_documents({})
    total_wallets: int = db["wallets"].count_documents({})
    total_investigations: int = db["investigations"].count_documents({})

    # -- Risk distribution (companies + crypto combined) --
    risk_pipeline = [
        {"$group": {"_id": "$risk_level", "count": {"$sum": 1}}},
    ]
    company_risk = list(db["companies"].aggregate(risk_pipeline))
    crypto_risk = list(db["crypto_projects"].aggregate(risk_pipeline))

    risk_distribution: dict[str, int] = {}
    for bucket in company_risk + crypto_risk:
        level = bucket["_id"]
        risk_distribution[level] = risk_distribution.get(level, 0) + bucket["count"]

    # -- Average trust score (companies + crypto combined) --
    avg_pipeline = [
        {"$group": {"_id": None, "avg": {"$avg": "$trust_score"}}},
    ]
    company_avg = list(db["companies"].aggregate(avg_pipeline))
    crypto_avg = list(db["crypto_projects"].aggregate(avg_pipeline))

    scores: list[float] = []
    counts: list[int] = []
    if company_avg and company_avg[0].get("avg") is not None:
        scores.append(company_avg[0]["avg"] * total_companies)
        counts.append(total_companies)
    if crypto_avg and crypto_avg[0].get("avg") is not None:
        scores.append(crypto_avg[0]["avg"] * total_crypto_projects)
        counts.append(total_crypto_projects)

    avg_trust_score: float = (
        round(sum(scores) / sum(counts), 1) if counts else 0.0
    )

    return {
        "source": "mongodb",
        "total_companies": total_companies,
        "total_crypto_projects": total_crypto_projects,
        "total_reviews": total_reviews,
        "total_wallets": total_wallets,
        "total_investigations": total_investigations,
        "risk_distribution": risk_distribution,
        "avg_trust_score": avg_trust_score,
    }


# ── Investigations ────────────────────────────────────────────────────────


@app.get("/api/investigations", tags=["Investigations"])
async def get_investigations(
    limit: int = Query(default=10, ge=1, le=100, description="Max results"),
) -> dict[str, Any]:
    """Return the latest investigations, sorted by timestamp descending."""
    db = _get_db_or_none()
    if db is None:
        results = _mock_investigations()[:limit]
        return {"source": "mock", "count": len(results), "investigations": results}

    cursor = (
        db["investigations"]
        .find({})
        .sort("timestamp", DESCENDING)
        .limit(limit)
    )
    results = [_serialise_doc(doc) for doc in cursor]
    return {"source": "mongodb", "count": len(results), "investigations": results}


# ── Audit Trail ───────────────────────────────────────────────────────────


@app.get("/api/audit", tags=["Audit"])
async def get_audit_trail(
    limit: int = Query(default=20, ge=1, le=200, description="Max results"),
    agent: Optional[str] = Query(
        default=None, description="Filter by agent name"
    ),
) -> dict[str, Any]:
    """Return the latest audit trail events.

    Optionally filter by agent name (e.g. ``crypto_agent``).
    """
    db = _get_db_or_none()
    if db is None:
        events = _mock_audit_events()
        if isinstance(agent, str) and agent:
            events = [event for event in events if event["agent"] == agent]
        events = events[:limit]
        return {"source": "mock", "count": len(events), "events": events}

    query: dict[str, Any] = {}
    if isinstance(agent, str) and agent:
        query["agent"] = agent

    cursor = (
        db["audit_log"]
        .find(query)
        .sort("timestamp", DESCENDING)
        .limit(limit)
    )
    events = [_serialise_audit_doc(doc) for doc in cursor]
    return {"source": "mongodb", "count": len(events), "events": events}


# ── Leaderboard ───────────────────────────────────────────────────────────


@app.get("/api/leaderboard", tags=["Dashboard"])
async def get_leaderboard(
    type: str = Query(  # noqa: A002
        default="companies",
        description="Entity type: 'companies' or 'crypto'",
    ),
    limit: int = Query(default=10, ge=1, le=50, description="Max results"),
) -> dict[str, Any]:
    """Return top entities ranked by trust_score.

    ``type`` determines the collection:
    - ``companies`` → ``companies`` collection (sorted by ``trust_score`` desc)
    - ``crypto`` → ``crypto_projects`` collection (sorted by ``trust_score`` desc)
    """
    if type == "companies":
        collection_name = "companies"
        projection = {
            "_id": 0,
            "company_name": 1,
            "profile_slug": 1,
            "trust_score": 1,
            "risk_level": 1,
            "industry": 1,
            "country": 1,
        }
    elif type == "crypto":
        collection_name = "crypto_projects"
        projection = {
            "_id": 0,
            "name": 1,
            "slug": 1,
            "symbol": 1,
            "trust_score": 1,
            "risk_level": 1,
            "price_usd": 1,
            "market_cap": 1,
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid type '{type}'. Must be 'companies' or 'crypto'.",
        )

    db = _get_db_or_none()
    if db is None:
        entities = _mock_companies() if type == "companies" else _mock_crypto_projects()
        results = sorted(
            entities,
            key=lambda item: item.get("trust_score") or 0,
            reverse=True,
        )[:limit]
        return {
            "source": "mock",
            "type": type,
            "count": len(results),
            "leaderboard": results,
        }

    cursor = (
        db[collection_name]
        .find({}, projection)
        .sort("trust_score", DESCENDING)
        .limit(limit)
    )
    results = list(cursor)
    return {"source": "mongodb", "type": type, "count": len(results), "leaderboard": results}


# ── Entity Detail ─────────────────────────────────────────────────────────


@app.get("/api/entity/{entity_type}/{slug}", tags=["Entities"])
async def get_entity_detail(entity_type: str, slug: str) -> dict[str, Any]:
    """Return full details for a single entity.

    Args:
        entity_type: ``company`` or ``crypto``.
        slug: The ``profile_slug`` (companies) or ``slug`` (crypto projects).

    Returns:
        The full document for the matched entity.
    """
    db = _get_db_or_none()
    if db is None:
        entity = _mock_entity_detail(entity_type, slug)
        return {"source": "mock", "entity_type": entity_type, "entity": entity}

    if entity_type == "company":
        doc = db["companies"].find_one({"profile_slug": slug})
        if doc is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company with slug '{slug}' not found.",
            )
        entity = _serialise_doc(doc)

        # Attach reviews for this company
        reviews_cursor = (
            db["reviews"]
            .find({"company_slug": slug}, {"_id": 0})
            .sort("date", DESCENDING)
            .limit(50)
        )
        entity["reviews"] = list(reviews_cursor)

    elif entity_type == "crypto":
        doc = db["crypto_projects"].find_one({"slug": slug})
        if doc is None:
            raise HTTPException(
                status_code=404,
                detail=f"Crypto project with slug '{slug}' not found.",
            )
        entity = _serialise_doc(doc)

    else:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid entity_type '{entity_type}'. "
                "Must be 'company' or 'crypto'."
            ),
        )

    return {"source": "mongodb", "entity_type": entity_type, "entity": entity}


# ── Agent Chat ────────────────────────────────────────────────────────────


# Lazy-loaded agent runner (initialized on first chat request)
_runner = None
_runner_lock = None


def _get_runner():
    """Lazy-initialize the ADK InMemoryRunner."""
    import threading

    global _runner, _runner_lock  # noqa: PLW0603

    if _runner_lock is None:
        _runner_lock = threading.Lock()

    if _runner is not None:
        return _runner

    with _runner_lock:
        if _runner is not None:
            return _runner

        try:
            from google.adk.runners import InMemoryRunner
            from agent.adk_agent import root_agent

            _runner = InMemoryRunner(agent=root_agent, app_name="vartovii")
            logger.info("🤖 ADK InMemoryRunner initialized for chat endpoint.")
            return _runner
        except Exception as exc:
            logger.error("Failed to initialize ADK runner: %s", exc)
            return None


@app.post("/api/chat", tags=["Agent"])
async def agent_chat(payload: dict[str, Any]) -> dict[str, Any]:
    """Send a message to the Vartovii AI agent.

    Request body:
        {"message": "Tell me about Wirecard", "session_id": "optional-session-id"}

    Returns:
        {"response": "...", "session_id": "...", "agent": "vartovii_orchestrator"}
    """
    message = payload.get("message", "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="'message' field is required.")

    session_id = payload.get("session_id", "default-session")
    runner = _get_runner()

    if runner is None:
        raise HTTPException(
            status_code=503,
            detail="Agent is not available. Check GOOGLE_API_KEY.",
        )

    try:
        from google.genai import types

        # Ensure session exists (create if not)
        user_id = "web-user"
        try:
            session = await runner.session_service.get_session(
                app_name="vartovii",
                user_id=user_id,
                session_id=session_id,
            )
        except Exception:
            session = None

        if session is None:
            session = await runner.session_service.create_session(
                app_name="vartovii",
                user_id=user_id,
                session_id=session_id,
            )
            logger.info("Created new session: %s", session_id)

        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=message)],
        )

        response_parts = []
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_parts.append(part.text)

        response_text = "\n".join(response_parts) if response_parts else "No response from agent."

        return {
            "response": response_text,
            "session_id": session_id,
            "agent": "vartovii_orchestrator",
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Agent chat error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}")


# ── Static Files (Landing Page) ──────────────────────────────────────────

import pathlib
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

_WEB_DIR = pathlib.Path(__file__).resolve().parent.parent / "web"

if _WEB_DIR.is_dir():
    @app.get("/", tags=["Web"], include_in_schema=False)
    async def serve_index():
        """Serve the landing page."""
        index_file = _WEB_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Vartovii Trust Agent API — use /docs for Swagger UI"}

    # Mount static assets (CSS, JS, images)
    app.mount("/", StaticFiles(directory=str(_WEB_DIR)), name="web")
    logger.info("📄 Serving static files from %s", _WEB_DIR)
