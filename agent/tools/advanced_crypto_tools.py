"""
Advanced Crypto Tools for Vartovii ADK Agent.

Extended analytics for deeper crypto intelligence:
- get_liquidity_analysis: DEX liquidity, volume, depth, impermanent loss
- get_whale_tracking: Top holders, whale concentration, movements
- get_defi_metrics: TVL, APY, protocol revenue, audit & exploit history

Data source priority:
  1. MongoDB Atlas (production / hackathon demo)
  2. Computed mock data (fallback when MongoDB is unavailable)
"""

import hashlib
import logging
from typing import Optional

from .db import get_collection, is_mongodb_available

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mock data generators — deterministic, slug-based
# ---------------------------------------------------------------------------

def _slug_hash(slug: str) -> int:
    """Deterministic hash from project slug for consistent mock data."""
    return int(hashlib.md5(slug.encode()).hexdigest(), 16)


def _mock_liquidity_data(slug: str) -> dict:
    """Generate realistic liquidity data based on project slug."""
    h = _slug_hash(slug)
    volume = 1_000_000 + (h % 500_000_000)
    return {
        "dex_liquidity_usd": volume * 3,
        "trading_volume_24h_usd": volume,
        "liquidity_depth": {
            "plus_2_pct_usd": int(volume * 0.15),
            "minus_2_pct_usd": int(volume * 0.12),
        },
        "impermanent_loss_risk": "LOW" if h % 3 == 0 else ("MEDIUM" if h % 3 == 1 else "HIGH"),
        "major_dex_pairs": _pick_dex_pairs(slug, h),
        "liquidity_score": round(40 + (h % 55), 1),
    }


def _pick_dex_pairs(slug: str, h: int) -> list[dict]:
    """Generate major DEX trading pairs."""
    symbol = slug.upper()[:4]
    dexes = ["Uniswap V3", "SushiSwap", "Curve", "Balancer", "PancakeSwap"]
    pairs = []
    for i in range(min(3, len(dexes))):
        idx = (h + i) % len(dexes)
        pairs.append({
            "pair": f"{symbol}/USDC",
            "dex": dexes[idx],
            "liquidity_usd": 500_000 + (h % 50_000_000),
            "volume_24h_usd": 100_000 + (h % 10_000_000),
        })
    return pairs


def _mock_whale_data(slug: str) -> dict:
    """Generate realistic whale tracking data based on project slug."""
    h = _slug_hash(slug)
    holders = []
    remaining = 100.0
    for i in range(10):
        pct = round(max(0.5, remaining * (0.15 - i * 0.012)), 2)
        remaining -= pct
        holders.append({
            "rank": i + 1,
            "address": f"0x{hashlib.md5(f'{slug}-{i}'.encode()).hexdigest()[:12]}...",
            "balance_pct": pct,
            "label": _whale_label(h, i),
        })
    concentration = round(sum(ho["balance_pct"] for ho in holders), 2)
    return {
        "top_10_holders": holders,
        "whale_concentration_pct": concentration,
        "recent_whale_movements": [
            {
                "direction": "BUY" if (h + i) % 2 == 0 else "SELL",
                "amount_usd": 500_000 + ((h + i) % 5_000_000),
                "timestamp": f"2026-05-{20 + (i % 10):02d}T{10 + i}:00:00Z",
            }
            for i in range(3)
        ],
        "accumulation_distribution_signal": (
            "ACCUMULATION" if h % 3 == 0
            else "DISTRIBUTION" if h % 3 == 1
            else "NEUTRAL"
        ),
    }


def _whale_label(h: int, idx: int) -> Optional[str]:
    """Assign labels to whale addresses."""
    labels = [
        "Treasury", "Foundation", "Binance Hot Wallet",
        "Coinbase Custody", "a16z Wallet", None,
        "Jump Trading", None, "Wintermute", None,
    ]
    return labels[(h + idx) % len(labels)]


def _mock_defi_data(slug: str) -> dict:
    """Generate realistic DeFi metrics based on project slug."""
    h = _slug_hash(slug)
    return {
        "tvl_usd": 10_000_000 + (h % 5_000_000_000),
        "apy_pct": round(1.5 + (h % 200) / 10, 2),
        "protocol_revenue_30d_usd": 100_000 + (h % 10_000_000),
        "audit_status": {
            "audited": h % 5 != 0,
            "auditor": _pick_auditor(h),
            "last_audit_date": f"2026-0{1 + h % 5}-15",
            "critical_findings": h % 7,
        },
        "exploit_history": _build_exploit_history(slug, h),
    }


def _pick_auditor(h: int) -> Optional[str]:
    """Pick an auditor name."""
    auditors = ["CertiK", "Trail of Bits", "OpenZeppelin", "Quantstamp", "Consensys Diligence"]
    if h % 5 == 0:
        return None  # not audited
    return auditors[h % len(auditors)]


def _build_exploit_history(slug: str, h: int) -> list[dict]:
    """Build exploit history (most projects have none)."""
    if h % 4 != 0:
        return []
    return [
        {
            "date": "2025-08-12",
            "type": "Flash Loan Attack" if h % 2 == 0 else "Reentrancy",
            "loss_usd": 1_000_000 + (h % 10_000_000),
            "recovered": h % 3 != 0,
        }
    ]


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

def get_liquidity_analysis(project_slug: str) -> dict:
    """
    Analyze DEX liquidity for a crypto project — trading volume,
    liquidity depth, impermanent loss risk, and major trading pairs.

    Args:
        project_slug: Project slug (e.g., "uniswap", "ethereum", "aave")

    Returns:
        DEX liquidity in USD, 24h trading volume, liquidity depth at ±2%,
        impermanent loss risk level, major DEX pairs with volumes.
    """
    slug = project_slug.strip().lower()

    # Try MongoDB first
    if is_mongodb_available():
        col = get_collection("crypto_projects")
        if col is not None:
            try:
                result = col.find_one(
                    {"slug": slug},
                    {"_id": 0, "name": 1, "symbol": 1, "slug": 1, "liquidity_data": 1},
                )
                if result and result.get("liquidity_data"):
                    return {
                        "found": True,
                        "project": result.get("name", project_slug),
                        "symbol": result.get("symbol", ""),
                        **result["liquidity_data"],
                        "source": "mongodb",
                    }
            except Exception as e:
                logger.warning("MongoDB get_liquidity_analysis failed: %s", e)

    # Fallback to computed mock data
    mock = _mock_liquidity_data(slug)
    return {
        "found": True,
        "project": project_slug,
        "symbol": slug.upper()[:4],
        **mock,
        "source": "mock",
    }


def get_whale_tracking(project_slug: str) -> dict:
    """
    Track whale activity for a crypto project — top holders,
    concentration risk, recent movements, accumulation/distribution.

    Args:
        project_slug: Project slug (e.g., "bitcoin", "uniswap", "solana")

    Returns:
        Top 10 holders with balance percentages and labels,
        whale concentration %, recent whale movements (buy/sell),
        accumulation/distribution signal.
    """
    slug = project_slug.strip().lower()

    # Try MongoDB first
    if is_mongodb_available():
        col = get_collection("crypto_projects")
        if col is not None:
            try:
                result = col.find_one(
                    {"slug": slug},
                    {"_id": 0, "name": 1, "symbol": 1, "slug": 1, "whale_data": 1},
                )
                if result and result.get("whale_data"):
                    return {
                        "found": True,
                        "project": result.get("name", project_slug),
                        "symbol": result.get("symbol", ""),
                        **result["whale_data"],
                        "source": "mongodb",
                    }
            except Exception as e:
                logger.warning("MongoDB get_whale_tracking failed: %s", e)

    # Fallback to computed mock data
    mock = _mock_whale_data(slug)
    return {
        "found": True,
        "project": project_slug,
        "symbol": slug.upper()[:4],
        **mock,
        "source": "mock",
    }


def get_defi_metrics(project_slug: str) -> dict:
    """
    Get DeFi protocol metrics — TVL, APY, revenue, audit status,
    and exploit history.

    Args:
        project_slug: Project slug (e.g., "aave", "uniswap", "lido")

    Returns:
        Total Value Locked (TVL), annual percentage yield (APY),
        30-day protocol revenue, audit status with findings,
        and historical exploit incidents.
    """
    slug = project_slug.strip().lower()

    # Try MongoDB first
    if is_mongodb_available():
        col = get_collection("crypto_projects")
        if col is not None:
            try:
                result = col.find_one(
                    {"slug": slug},
                    {"_id": 0, "name": 1, "symbol": 1, "slug": 1, "defi_data": 1},
                )
                if result and result.get("defi_data"):
                    return {
                        "found": True,
                        "project": result.get("name", project_slug),
                        "symbol": result.get("symbol", ""),
                        **result["defi_data"],
                        "source": "mongodb",
                    }
            except Exception as e:
                logger.warning("MongoDB get_defi_metrics failed: %s", e)

    # Fallback to computed mock data
    mock = _mock_defi_data(slug)
    return {
        "found": True,
        "project": project_slug,
        "symbol": slug.upper()[:4],
        **mock,
        "source": "mock",
    }
