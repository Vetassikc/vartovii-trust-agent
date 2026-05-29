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
            "Data endpoints will return 503."
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
    return {
        "status": "ok",
        "mongodb": _is_connected(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Stats ─────────────────────────────────────────────────────────────────


@app.get("/api/stats", tags=["Dashboard"])
async def get_stats() -> dict[str, Any]:
    """Aggregate statistics across all collections.

    Returns total counts, risk distribution, and average trust score
    computed via MongoDB aggregation pipelines.
    """
    db = _get_db()

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
    db = _get_db()
    cursor = (
        db["investigations"]
        .find({})
        .sort("timestamp", DESCENDING)
        .limit(limit)
    )
    results = [_serialise_doc(doc) for doc in cursor]
    return {"count": len(results), "investigations": results}


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
    db = _get_db()

    query: dict[str, Any] = {}
    if agent:
        query["agent"] = agent

    cursor = (
        db["audit_log"]
        .find(query)
        .sort("timestamp", DESCENDING)
        .limit(limit)
    )
    events = [_serialise_doc(doc) for doc in cursor]
    return {"count": len(events), "events": events}


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
    db = _get_db()

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

    cursor = (
        db[collection_name]
        .find({}, projection)
        .sort("trust_score", DESCENDING)
        .limit(limit)
    )
    results = list(cursor)
    return {"type": type, "count": len(results), "leaderboard": results}


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
    db = _get_db()

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

    return {"entity_type": entity_type, "entity": entity}
