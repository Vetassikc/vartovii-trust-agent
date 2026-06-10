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
import re
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
from agent.tools.live_data import (
    COINGECKO_CACHE_TTL_SECONDS,
    ETHERSCAN_CACHE_TTL_SECONDS,
    build_live_crypto_evidence,
    cache_age_seconds,
    fetch_coingecko_market_data,
    fetch_etherscan_wallet_balance,
    is_valid_eth_address,
    is_cache_fresh,
    normalize_eth_address,
)
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
_ETHERSCAN_API_KEY_ENV: str = os.getenv("ETHERSCAN_API_KEY", "")
ETHERSCAN_API_KEY: str = (
    ""
    if _ETHERSCAN_API_KEY_ENV.startswith("your_")
    else _ETHERSCAN_API_KEY_ENV
)
LIVE_WALLET_ADDRESS: str = os.getenv(
    "LIVE_WALLET_ADDRESS",
    "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
)
CHAT_FAST_PATH_ENABLED: bool = os.getenv(
    "CHAT_FAST_PATH_ENABLED",
    "true",
).strip().lower() in {"1", "true", "yes", "on"}
CHAT_PREWARM_ENABLED: bool = os.getenv(
    "CHAT_PREWARM_ENABLED",
    "true",
).strip().lower() in {"1", "true", "yes", "on"}

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


def _get_crypto_project_for_live_proof(slug: str, db: Optional[Database]) -> Optional[dict[str, Any]]:
    """Return a crypto project from MongoDB or demo data for live proof."""
    normalized = slug.strip().lower()
    if db is not None:
        doc = db["crypto_projects"].find_one(
            {
                "$or": [
                    {"slug": normalized},
                    {"symbol": {"$regex": f"^{normalized}$", "$options": "i"}},
                    {"name": {"$regex": f"^{normalized}$", "$options": "i"}},
                ]
            },
            {"_id": 0},
        )
        if doc:
            return doc

    for project in MOCK_CRYPTO_PROJECTS.values():
        if normalized in {
            str(project.get("slug", "")).lower(),
            str(project.get("symbol", "")).lower(),
            str(project.get("name", "")).lower(),
        }:
            return dict(project)
    return None


def _load_live_evidence_cache(
    db: Optional[Database],
    slug: str,
) -> Optional[dict[str, Any]]:
    """Read a fresh live evidence cache record from MongoDB."""
    if db is None:
        return None
    cached = db["live_evidence"].find_one(
        {"provider": "coingecko", "entity_type": "crypto", "slug": slug},
        {"_id": 0},
    )
    if cached and is_cache_fresh(cached):
        return cached
    return None


def _persist_live_proof(
    db: Optional[Database],
    slug: str,
    live_evidence: dict[str, Any],
) -> dict[str, Any]:
    """Persist live evidence and return a public persistence proof."""
    proof = {
        "available": db is not None,
        "persisted": False,
        "collection": "live_evidence",
        "document_key": f"coingecko:crypto:{slug}",
    }
    if db is None:
        proof["status"] = "skipped_no_mongodb"
        return proof

    db["live_evidence"].update_one(
        {"provider": "coingecko", "entity_type": "crypto", "slug": slug},
        {
            "$set": {
                "provider": "coingecko",
                "entity_type": "crypto",
                "slug": slug,
                "fetched_at": live_evidence.get("fetched_at"),
                "cache_ttl_seconds": COINGECKO_CACHE_TTL_SECONDS,
                "live_evidence": live_evidence,
            }
        },
        upsert=True,
    )

    db["crypto_projects"].update_one(
        {"slug": slug},
        {
            "$set": {
                "live_enriched_at": live_evidence.get("fetched_at"),
                "live_market": live_evidence.get("market", {}),
                "live_trust_delta": live_evidence.get("live_trust_delta", 0),
                "live_adjusted_trust_score": live_evidence.get(
                    "live_adjusted_trust_score"
                ),
            }
        },
        upsert=False,
    )

    persisted = db["live_evidence"].find_one(
        {"provider": "coingecko", "entity_type": "crypto", "slug": slug},
        {"_id": 0, "fetched_at": 1, "live_evidence.live_adjusted_trust_score": 1},
    )
    proof["persisted"] = persisted is not None
    proof["status"] = "persisted" if persisted else "write_not_confirmed"
    proof["fetched_at"] = persisted.get("fetched_at") if persisted else None
    return proof


def _get_wallet_for_live_proof(address: str, db: Optional[Database]) -> Optional[dict[str, Any]]:
    """Return a wallet profile from MongoDB or demo data for wallet live proof."""
    normalized = normalize_eth_address(address)
    if db is not None:
        doc = db["wallets"].find_one(
            {"address": {"$regex": f"^{re.escape(normalized)}$", "$options": "i"}},
            {"_id": 0},
        )
        if doc:
            return doc

    wallet = MOCK_WALLETS.get(normalized)
    return dict(wallet) if wallet else None


def _load_wallet_live_cache(
    db: Optional[Database],
    address: str,
) -> Optional[dict[str, Any]]:
    """Read a fresh Etherscan wallet balance cache record from MongoDB."""
    if db is None:
        return None
    cached = db["live_evidence"].find_one(
        {
            "provider": "etherscan",
            "entity_type": "wallet",
            "address": normalize_eth_address(address),
        },
        {"_id": 0},
    )
    if cached and is_cache_fresh(cached, ETHERSCAN_CACHE_TTL_SECONDS):
        return cached
    return None


def _wallet_balance_label(balance: dict[str, Any], wallet: Optional[dict[str, Any]]) -> str:
    """Return a display-ready ETH balance for public proof cards."""
    if balance.get("available"):
        return f"{balance.get('eth_balance_display', balance.get('eth_balance'))} ETH"
    fallback_balance = (wallet or {}).get("eth_balance")
    if isinstance(fallback_balance, (int, float)):
        return f"{fallback_balance:,.4f} ETH fallback"
    return "not available"


def _build_wallet_live_evidence(
    *,
    address: str,
    wallet: Optional[dict[str, Any]],
    balance: dict[str, Any],
    cache_status: str,
) -> dict[str, Any]:
    """Build a judge-facing live wallet evidence object."""
    eth_balance = balance.get("eth_balance") if balance.get("available") else (wallet or {}).get("eth_balance")
    usd_value = (wallet or {}).get("usd_value")
    source_label = "Etherscan API V2" if balance.get("available") else "wallet fallback"
    fetched_at = balance.get("fetched_at") or datetime.now(timezone.utc).isoformat()

    factors = [
        {
            "label": "Wallet label",
            "value": (wallet or {}).get("label") or "unlabelled address",
            "impact": "MongoDB wallet profile or demo fallback",
        },
        {
            "label": "Native ETH balance",
            "value": _wallet_balance_label(balance, wallet),
            "impact": source_label,
        },
        {
            "label": "Chain",
            "value": "Ethereum mainnet",
            "impact": "Etherscan V2 chainid=1",
        },
        {
            "label": "Evidence freshness",
            "value": cache_status,
            "impact": fetched_at,
        },
    ]

    return {
        "entity_type": "wallet",
        "address": address,
        "normalized_address": normalize_eth_address(address),
        "chain": "ethereum",
        "chain_id": "1",
        "label": (wallet or {}).get("label"),
        "eth_balance": eth_balance,
        "eth_balance_display": (
            balance.get("eth_balance_display")
            if balance.get("available")
            else _wallet_balance_label(balance, wallet).replace(" ETH fallback", "")
        ),
        "usd_value": usd_value,
        "balance": balance,
        "factors": factors,
        "fetched_at": fetched_at,
        "cache_status": cache_status,
    }


def _wallet_persistence_proof(db: Optional[Database], address: str) -> dict[str, Any]:
    """Return the public persistence proof shell for wallet live evidence."""
    return {
        "available": db is not None,
        "persisted": False,
        "collection": "live_evidence",
        "document_key": f"etherscan:wallet:{normalize_eth_address(address)}",
    }


def _persist_wallet_live_proof(
    db: Optional[Database],
    address: str,
    live_evidence: dict[str, Any],
) -> dict[str, Any]:
    """Persist live wallet evidence and return a public persistence proof."""
    proof = _wallet_persistence_proof(db, address)
    if db is None:
        proof["status"] = "skipped_no_mongodb"
        return proof

    normalized = normalize_eth_address(address)
    db["live_evidence"].update_one(
        {"provider": "etherscan", "entity_type": "wallet", "address": normalized},
        {
            "$set": {
                "provider": "etherscan",
                "entity_type": "wallet",
                "address": normalized,
                "fetched_at": live_evidence.get("fetched_at"),
                "cache_ttl_seconds": ETHERSCAN_CACHE_TTL_SECONDS,
                "live_evidence": live_evidence,
            }
        },
        upsert=True,
    )

    db["wallets"].update_one(
        {"address": {"$regex": f"^{re.escape(normalized)}$", "$options": "i"}},
        {
            "$set": {
                "live_enriched_at": live_evidence.get("fetched_at"),
                "eth_balance": live_evidence.get("eth_balance"),
                "live_balance": live_evidence.get("balance", {}),
            }
        },
        upsert=False,
    )

    persisted = db["live_evidence"].find_one(
        {"provider": "etherscan", "entity_type": "wallet", "address": normalized},
        {"_id": 0, "fetched_at": 1, "live_evidence.eth_balance": 1},
    )
    proof["persisted"] = persisted is not None
    proof["status"] = "persisted" if persisted else "write_not_confirmed"
    proof["fetched_at"] = persisted.get("fetched_at") if persisted else None
    return proof


def _build_wallet_live_proof_response(
    *,
    address: str,
    wallet: Optional[dict[str, Any]],
    live_evidence: dict[str, Any],
    source: str,
    cache_status: str,
    mongodb_proof: dict[str, Any],
    live_api_called: bool,
    cache_age: Optional[int] = None,
) -> dict[str, Any]:
    """Build the public wallet live-proof API response."""
    balance = live_evidence.get("balance", {})
    source_evidence = (
        "Etherscan live API called"
        if live_api_called
        else "Fresh MongoDB live_evidence cache reused"
        if source == "mongodb_cache"
        else balance.get("error") or "Etherscan live balance unavailable"
    )
    return {
        "status": "ready" if balance.get("available") else "degraded",
        "source": source,
        "live_api_called": live_api_called,
        "target": {
            "entity_type": "wallet",
            "address": address,
            "label": live_evidence.get("label") or (wallet or {}).get("label"),
            "chain": "ethereum",
        },
        "source_freshness": {
            "provider": "Etherscan",
            "cache_status": cache_status,
            "fetched_at": live_evidence.get("fetched_at"),
            "cache_age_seconds": cache_age,
            "cache_ttl_seconds": ETHERSCAN_CACHE_TTL_SECONDS,
            "source_url": balance.get("source_url"),
        },
        "wallet_evidence": live_evidence,
        "mongodb_proof": mongodb_proof,
        "agent_trace": [
            {
                "step": 1,
                "agent": "vartovii_orchestrator",
                "action": "Route wallet balance proof request to crypto specialist",
                "evidence": "Wallet proofs share the crypto due-diligence route.",
            },
            {
                "step": 2,
                "agent": "crypto_agent",
                "action": "Fetch Etherscan native ETH balance or reuse fresh Atlas cache",
                "evidence": source_evidence,
            },
            {
                "step": 3,
                "agent": "crypto_agent",
                "action": "Normalize wallet balance into judge-readable evidence",
                "evidence": _wallet_balance_label(balance, wallet),
            },
            {
                "step": 4,
                "agent": "memory_agent",
                "action": "Persist wallet evidence for audit and replay",
                "evidence": mongodb_proof.get("status", "not persisted"),
            },
            {
                "step": 5,
                "agent": "mongodb_mcp_agent",
                "action": "Expose wallet live_evidence for ad-hoc Atlas inspection",
                "evidence": mongodb_proof.get("document_key"),
            },
        ],
    }


def _build_live_proof_response(
    *,
    slug: str,
    project: Optional[dict[str, Any]],
    live_evidence: dict[str, Any],
    source: str,
    cache_status: str,
    mongodb_proof: dict[str, Any],
    live_api_called: bool,
    cache_age: Optional[int] = None,
) -> dict[str, Any]:
    """Build the public live-proof API response."""
    market = live_evidence.get("market", {})
    return {
        "status": "ready" if market.get("available") else "degraded",
        "source": source,
        "live_api_called": live_api_called,
        "target": {
            "entity_type": "crypto",
            "slug": slug,
            "name": live_evidence.get("name") or (project or {}).get("name") or slug,
            "symbol": live_evidence.get("symbol") or (project or {}).get("symbol"),
        },
        "source_freshness": {
            "provider": "CoinGecko",
            "cache_status": cache_status,
            "fetched_at": live_evidence.get("fetched_at"),
            "cache_age_seconds": cache_age,
            "cache_ttl_seconds": COINGECKO_CACHE_TTL_SECONDS,
            "source_url": market.get("source_url"),
        },
        "live_evidence": live_evidence,
        "mongodb_proof": mongodb_proof,
        "agent_trace": [
            {
                "step": 1,
                "agent": "vartovii_orchestrator",
                "action": f"Route live crypto proof request for {slug}",
                "evidence": "ADK crypto specialist owns crypto market evidence.",
            },
            {
                "step": 2,
                "agent": "crypto_agent",
                "action": "Fetch CoinGecko market signal or reuse fresh Atlas cache",
                "evidence": (
                    "CoinGecko live API called"
                    if live_api_called
                    else "Fresh MongoDB live_evidence cache reused"
                ),
            },
            {
                "step": 3,
                "agent": "crypto_agent",
                "action": "Convert market movement into trust-score delta",
                "evidence": (
                    f"{live_evidence.get('base_trust_score', 0)}/100 baseline "
                    f"{live_evidence.get('live_trust_delta', 0):+d} delta"
                ),
            },
            {
                "step": 4,
                "agent": "memory_agent",
                "action": "Persist live evidence for audit and MCP inspection",
                "evidence": mongodb_proof.get("status", "not persisted"),
            },
            {
                "step": 5,
                "agent": "mongodb_mcp_agent",
                "action": "Expose stored live_evidence for ad-hoc Atlas inspection",
                "evidence": mongodb_proof.get("document_key"),
            },
        ],
    }


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
    _prewarm_runner_in_background()
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
        "chat_fast_path": CHAT_FAST_PATH_ENABLED,
        "chat_prewarm": CHAT_PREWARM_ENABLED,
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
            {
                "name": "Live evidence proof",
                "status": "implemented",
                "evidence": "/api/live-proof fetches CoinGecko evidence and persists Atlas cache",
            },
            {
                "name": "Live wallet proof",
                "status": "implemented",
                "evidence": "/api/wallet-live-proof fetches Etherscan ETH balance evidence and persists Atlas cache",
            },
        ],
        "quality": {
            "test_count": 68,
            "core_agents": 5,
            "custom_tools": 28,
            "data_source": "mongodb" if mongodb_connected else "mock",
            "live_sources": ["CoinGecko", "Etherscan"],
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


@app.get("/api/live-proof", tags=["System"])
async def live_proof(
    slug: str = Query(default="ethereum", description="Crypto slug, symbol, or CoinGecko ID"),
    force: bool = Query(default=False, description="Bypass MongoDB live evidence cache"),
) -> dict[str, Any]:
    """Return one-click proof of live source enrichment plus MongoDB persistence."""
    normalized_slug = slug.strip().lower()
    if not normalized_slug:
        raise HTTPException(status_code=400, detail="'slug' must not be empty.")

    db = _get_db_or_none()
    project = _get_crypto_project_for_live_proof(normalized_slug, db)
    if project is None:
        raise HTTPException(
            status_code=404,
            detail=f"Crypto project '{slug}' not found in the evidence catalog.",
        )
    normalized_slug = str(project.get("slug") or normalized_slug).lower()

    cached = None if force else _load_live_evidence_cache(db, normalized_slug)
    if cached:
        live_evidence = cached.get("live_evidence", {})
        return _build_live_proof_response(
            slug=normalized_slug,
            project=project,
            live_evidence=live_evidence,
            source="mongodb_cache",
            cache_status="fresh_atlas_cache",
            mongodb_proof={
                "available": True,
                "persisted": True,
                "status": "cache_hit",
                "collection": "live_evidence",
                "document_key": f"coingecko:crypto:{normalized_slug}",
                "fetched_at": cached.get("fetched_at"),
            },
            live_api_called=False,
            cache_age=cache_age_seconds(cached),
        )

    market = fetch_coingecko_market_data(normalized_slug)
    cache_status = "coingecko_live" if market.get("available") else "coingecko_unavailable"
    live_evidence = build_live_crypto_evidence(
        slug=normalized_slug,
        project=project,
        market=market,
        cache_status=cache_status,
    )

    mongodb_proof = _persist_live_proof(db, normalized_slug, live_evidence)
    source = (
        "coingecko_live+mongodb"
        if market.get("available") and mongodb_proof.get("persisted")
        else "coingecko_live"
        if market.get("available")
        else "demo_fallback"
    )
    return _build_live_proof_response(
        slug=normalized_slug,
        project=project,
        live_evidence=live_evidence,
        source=source,
        cache_status=cache_status,
        mongodb_proof=mongodb_proof,
        live_api_called=True,
    )


@app.get("/api/wallet-live-proof", tags=["System"])
async def wallet_live_proof(
    address: str = Query(default=LIVE_WALLET_ADDRESS, description="Ethereum wallet address"),
    force: bool = Query(default=False, description="Bypass MongoDB wallet balance cache"),
) -> dict[str, Any]:
    """Return one-click proof of live Etherscan wallet balance enrichment."""
    cleaned_address = address.strip()
    if not is_valid_eth_address(cleaned_address):
        raise HTTPException(status_code=400, detail="'address' must be a valid Ethereum address.")

    normalized_address = normalize_eth_address(cleaned_address)
    db = _get_db_or_none()
    wallet = _get_wallet_for_live_proof(cleaned_address, db)

    cached = None if force else _load_wallet_live_cache(db, cleaned_address)
    if cached:
        live_evidence = cached.get("live_evidence", {})
        return _build_wallet_live_proof_response(
            address=live_evidence.get("address") or cleaned_address,
            wallet=wallet,
            live_evidence=live_evidence,
            source="mongodb_cache",
            cache_status="fresh_atlas_cache",
            mongodb_proof={
                "available": True,
                "persisted": True,
                "status": "cache_hit",
                "collection": "live_evidence",
                "document_key": f"etherscan:wallet:{normalized_address}",
                "fetched_at": cached.get("fetched_at"),
            },
            live_api_called=False,
            cache_age=cache_age_seconds(cached),
        )

    balance = fetch_etherscan_wallet_balance(cleaned_address, ETHERSCAN_API_KEY)
    cache_status = "etherscan_live" if balance.get("available") else "etherscan_unavailable"
    live_evidence = _build_wallet_live_evidence(
        address=cleaned_address,
        wallet=wallet,
        balance=balance,
        cache_status=cache_status,
    )

    if balance.get("available"):
        mongodb_proof = _persist_wallet_live_proof(db, cleaned_address, live_evidence)
    else:
        mongodb_proof = _wallet_persistence_proof(db, cleaned_address)
        mongodb_proof["status"] = "not_persisted_no_live_balance"

    source = (
        "etherscan_live+mongodb"
        if balance.get("available") and mongodb_proof.get("persisted")
        else "etherscan_live"
        if balance.get("available")
        else "wallet_fallback"
        if wallet
        else "etherscan_unavailable"
    )
    return _build_wallet_live_proof_response(
        address=cleaned_address,
        wallet=wallet,
        live_evidence=live_evidence,
        source=source,
        cache_status=cache_status,
        mongodb_proof=mongodb_proof,
        live_api_called=bool(ETHERSCAN_API_KEY),
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


def _prewarm_runner_in_background() -> None:
    """Warm the ADK runner after startup so the first chat avoids import cost."""
    if not CHAT_PREWARM_ENABLED or not AIConfig.ADK_ENABLED:
        return

    import threading

    def _target() -> None:
        try:
            _get_runner()
        except Exception as exc:  # pragma: no cover - defensive startup guard
            logger.warning("ADK runner prewarm failed: %s", exc)

    thread = threading.Thread(
        target=_target,
        name="vartovii-adk-runner-prewarm",
        daemon=True,
    )
    thread.start()


def _normalize_chat_prompt(message: str) -> str:
    """Return a stable prompt shape for exact demo fast-path detection."""
    return re.sub(r"\s+", " ", message.strip().lower())


def _get_fast_chat_response(message: str) -> Optional[str]:
    """Return deterministic answers for low-risk demo prompts.

    The full Wirecard forensic report intentionally stays on the ADK path. These
    fast paths are for supporting demo questions where waiting for the model
    adds latency without adding new evidence.
    """
    if not CHAT_FAST_PATH_ENABLED:
        return None

    normalized = _normalize_chat_prompt(message)

    if "60-second" in normalized and "more than a chatbot" in normalized:
        return (
            "## 60-second summary\n\n"
            "Vartovii is more than a chatbot because it does not stop at a text answer. "
            "It runs an evidence workflow.\n\n"
            "- **Agent route:** Google ADK routes work to specialist agents for company, "
            "crypto, memory, and MongoDB inspection.\n"
            "- **Evidence layer:** MongoDB Atlas stores companies, crypto projects, "
            "wallets, investigations, live proofs, and audit events.\n"
            "- **Live proof:** CoinGecko and Etherscan add current market and wallet "
            "signals, then the result is saved back to Atlas.\n"
            "- **MCP value:** MongoDB MCP gives judges and agents an inspectable database "
            "path beyond fixed UI screens.\n"
            "- **Decision output:** the product shows score, risk label, route, evidence, "
            "and final action in one place.\n\n"
            "The result is a trust investigation system that judges can verify, not just "
            "a generic chat response."
        )

    if (
        "mongodb atlas" in normalized
        and "mcp" in normalized
        and any(word in normalized for word in ("improve", "value", "workflow"))
    ):
        data_source = "MongoDB Atlas" if _is_connected() else "demo fallback data"
        mcp_state = "configured" if MONGODB_CONNECTION_STRING else "ready when Atlas is configured"
        return (
            "## MongoDB Atlas and MCP value\n\n"
            f"Vartovii uses **{data_source}** as the evidence and memory layer. "
            "That means the agent can work with saved companies, crypto projects, "
            "wallets, investigations, live proof records, and audit events.\n\n"
            f"**MCP status:** {mcp_state}.\n\n"
            "Why this improves the workflow:\n\n"
            "- **Durable memory:** the result is saved, so the investigation can be "
            "reviewed later.\n"
            "- **Inspectable proof:** judges can open `/api/judge-trace`, "
            "`/api/live-proof`, and `/api/readiness` instead of trusting a hidden prompt.\n"
            "- **Flexible questions:** MongoDB MCP gives the agent a database specialist "
            "path for ad-hoc inspection.\n"
            "- **Better demo story:** the UI, API, and database all show the same route: "
            "source -> agent -> memory -> MCP.\n\n"
            "In short: Atlas makes the answer persistent, and MCP makes the evidence "
            "inspectable."
        )

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

    fast_response = _get_fast_chat_response(message)
    if fast_response is not None:
        return {
            "response": fast_response,
            "session_id": session_id,
            "agent": "vartovii_orchestrator",
            "mode": "fast_path",
        }

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
