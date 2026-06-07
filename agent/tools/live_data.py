"""
Live market evidence helpers for Vartovii trust investigations.

The helpers are intentionally small and dependency-free so Cloud Run can fetch
public evidence without adding another production package. MongoDB persistence
is handled by callers because the agent tools and dashboard API use different
connection managers.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
COINGECKO_CACHE_TTL_SECONDS = 3600
ETHERSCAN_BASE_URL = "https://api.etherscan.io/v2/api"
ETHERSCAN_CACHE_TTL_SECONDS = 900
ETHERSCAN_CHAIN_ID = "1"
WEI_PER_ETH = 10**18
ETH_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")

COINGECKO_ID_ALIASES = {
    "btc": "bitcoin",
    "bitcoin": "bitcoin",
    "eth": "ethereum",
    "ethereum": "ethereum",
    "uni": "uniswap",
    "uniswap": "uniswap",
}


def utc_now_iso() -> str:
    """Return the current UTC time in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def normalize_coingecko_id(slug: str) -> str:
    """Normalize local slugs or symbols into CoinGecko IDs."""
    key = str(slug or "").strip().lower()
    return COINGECKO_ID_ALIASES.get(key, key.replace(" ", "-"))


def normalize_eth_address(address: str) -> str:
    """Normalize an Ethereum address for cache keys."""
    return str(address or "").strip().lower()


def is_valid_eth_address(address: str) -> bool:
    """Return whether the value has the shape of an Ethereum address."""
    return bool(ETH_ADDRESS_RE.fullmatch(str(address or "").strip()))


def _safe_float(value: Any) -> Optional[float]:
    """Convert numeric API values to float while preserving missing values."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_iso_datetime(value: Any) -> Optional[datetime]:
    """Parse an ISO timestamp into an aware datetime if possible."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def cache_age_seconds(cached_doc: dict[str, Any]) -> Optional[int]:
    """Return cache age in seconds from a live evidence cache document."""
    fetched_at = parse_iso_datetime(
        cached_doc.get("fetched_at")
        or cached_doc.get("market", {}).get("fetched_at")
        or cached_doc.get("live_evidence", {}).get("fetched_at")
    )
    if fetched_at is None:
        return None
    return max(0, int((datetime.now(timezone.utc) - fetched_at).total_seconds()))


def is_cache_fresh(cached_doc: dict[str, Any], ttl_seconds: int = COINGECKO_CACHE_TTL_SECONDS) -> bool:
    """Return whether a MongoDB live evidence cache document is fresh."""
    age = cache_age_seconds(cached_doc)
    return age is not None and age <= ttl_seconds


def fetch_coingecko_market_data(slug: str, timeout_seconds: float = 8.0) -> dict[str, Any]:
    """Fetch live market data from CoinGecko's public API.

    Args:
        slug: Local project slug, symbol, or CoinGecko ID.
        timeout_seconds: HTTP timeout.

    Returns:
        A serialisable evidence object. ``available`` is false when CoinGecko is
        unreachable or does not return the requested asset.
    """
    coingecko_id = normalize_coingecko_id(slug)
    params = urlencode(
        {
            "ids": coingecko_id,
            "vs_currencies": "usd",
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
            "include_last_updated_at": "true",
        }
    )
    url = f"{COINGECKO_BASE_URL}/simple/price?{params}"
    requested_at = utc_now_iso()
    request = Request(
        url,
        headers={
            "User-Agent": "vartovii-trust-agent/2.0 hackathon-live-evidence",
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - fixed public HTTPS endpoint
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("CoinGecko live evidence fetch failed for %s: %s", coingecko_id, exc)
        return {
            "available": False,
            "provider": "coingecko",
            "coingecko_id": coingecko_id,
            "requested_slug": slug,
            "fetched_at": requested_at,
            "source_url": url,
            "error": exc.__class__.__name__,
        }

    asset = payload.get(coingecko_id)
    if not isinstance(asset, dict):
        return {
            "available": False,
            "provider": "coingecko",
            "coingecko_id": coingecko_id,
            "requested_slug": slug,
            "fetched_at": requested_at,
            "source_url": url,
            "error": "asset_not_found",
        }

    last_updated = asset.get("last_updated_at")
    last_updated_iso = None
    if isinstance(last_updated, (int, float)):
        last_updated_iso = datetime.fromtimestamp(last_updated, timezone.utc).isoformat()

    return {
        "available": True,
        "provider": "coingecko",
        "coingecko_id": coingecko_id,
        "requested_slug": slug,
        "fetched_at": requested_at,
        "source_url": url,
        "price_usd": _safe_float(asset.get("usd")),
        "market_cap_usd": _safe_float(asset.get("usd_market_cap")),
        "volume_24h_usd": _safe_float(asset.get("usd_24h_vol")),
        "price_change_24h_pct": _safe_float(asset.get("usd_24h_change")),
        "coingecko_last_updated_at": last_updated_iso,
    }


def _format_eth_from_wei(balance_wei: int) -> str:
    """Format wei as an ETH decimal string without losing trailing precision."""
    whole = balance_wei // WEI_PER_ETH
    fractional = balance_wei % WEI_PER_ETH
    if fractional == 0:
        return str(whole)
    return f"{whole}.{fractional:018d}".rstrip("0")


def fetch_etherscan_wallet_balance(
    address: str,
    api_key: str,
    timeout_seconds: float = 8.0,
) -> dict[str, Any]:
    """Fetch a live Ethereum wallet balance from Etherscan API V2."""
    cleaned_address = str(address or "").strip()
    requested_at = utc_now_iso()
    safe_params = {
        "chainid": ETHERSCAN_CHAIN_ID,
        "module": "account",
        "action": "balance",
        "address": cleaned_address,
        "tag": "latest",
    }
    source_url = f"{ETHERSCAN_BASE_URL}?{urlencode(safe_params)}"

    if not is_valid_eth_address(cleaned_address):
        return {
            "available": False,
            "provider": "etherscan",
            "chain_id": ETHERSCAN_CHAIN_ID,
            "address": cleaned_address,
            "fetched_at": requested_at,
            "source_url": source_url,
            "error": "invalid_address",
        }

    if not api_key:
        return {
            "available": False,
            "provider": "etherscan",
            "chain_id": ETHERSCAN_CHAIN_ID,
            "address": cleaned_address,
            "fetched_at": requested_at,
            "source_url": source_url,
            "error": "missing_api_key",
        }

    request_params = {**safe_params, "apikey": api_key}
    request = Request(
        f"{ETHERSCAN_BASE_URL}?{urlencode(request_params)}",
        headers={
            "User-Agent": "vartovii-trust-agent/2.0 hackathon-wallet-proof",
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - fixed public HTTPS endpoint
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("Etherscan wallet balance fetch failed for %s: %s", cleaned_address, exc)
        return {
            "available": False,
            "provider": "etherscan",
            "chain_id": ETHERSCAN_CHAIN_ID,
            "address": cleaned_address,
            "fetched_at": requested_at,
            "source_url": source_url,
            "error": exc.__class__.__name__,
        }

    if str(payload.get("status")) != "1":
        return {
            "available": False,
            "provider": "etherscan",
            "chain_id": ETHERSCAN_CHAIN_ID,
            "address": cleaned_address,
            "fetched_at": requested_at,
            "source_url": source_url,
            "error": str(payload.get("message") or "etherscan_not_ok"),
        }

    try:
        balance_wei = int(str(payload.get("result", "0")))
    except (TypeError, ValueError):
        return {
            "available": False,
            "provider": "etherscan",
            "chain_id": ETHERSCAN_CHAIN_ID,
            "address": cleaned_address,
            "fetched_at": requested_at,
            "source_url": source_url,
            "error": "invalid_balance_result",
        }

    return {
        "available": True,
        "provider": "etherscan",
        "chain_id": ETHERSCAN_CHAIN_ID,
        "address": cleaned_address,
        "fetched_at": requested_at,
        "source_url": source_url,
        "balance_wei": str(balance_wei),
        "eth_balance": balance_wei / WEI_PER_ETH,
        "eth_balance_display": _format_eth_from_wei(balance_wei),
    }


def trust_delta_from_market(market: dict[str, Any]) -> int:
    """Translate live market movement into a small trust-score adjustment."""
    change = _safe_float(market.get("price_change_24h_pct"))
    if change is None:
        return 0
    if change <= -20:
        return -8
    if change <= -10:
        return -4
    if change >= 15:
        return 3
    if change >= 8:
        return 2
    return 0


def clamp_score(score: float) -> int:
    """Clamp a trust score to the public 0-100 scale."""
    return max(0, min(100, int(round(score))))


def build_live_crypto_evidence(
    *,
    slug: str,
    project: Optional[dict[str, Any]],
    market: dict[str, Any],
    cache_status: str,
) -> dict[str, Any]:
    """Build a judge-facing live evidence object from project and market data."""
    base_score = int((project or {}).get("trust_score") or 0)
    delta = trust_delta_from_market(market) if market.get("available") else 0
    adjusted_score = clamp_score(base_score + delta)
    price_change = _safe_float(market.get("price_change_24h_pct"))

    factors = [
        {
            "label": "Stored trust baseline",
            "value": f"{base_score}/100",
            "impact": "MongoDB entity score",
        },
        {
            "label": "Live market movement",
            "value": (
                f"{price_change:+.2f}% in 24h"
                if price_change is not None
                else "not reported"
            ),
            "impact": f"{delta:+d} trust delta",
        },
        {
            "label": "Live price",
            "value": (
                f"${market['price_usd']:,.4f}"
                if isinstance(market.get("price_usd"), (int, float))
                else "not reported"
            ),
            "impact": "CoinGecko public API",
        },
        {
            "label": "Evidence freshness",
            "value": cache_status,
            "impact": market.get("fetched_at") or "timestamp pending",
        },
    ]

    return {
        "entity_type": "crypto",
        "slug": slug,
        "name": (project or {}).get("name") or market.get("coingecko_id") or slug,
        "symbol": (project or {}).get("symbol"),
        "base_trust_score": base_score,
        "live_trust_delta": delta,
        "live_adjusted_trust_score": adjusted_score,
        "risk_level": (project or {}).get("risk_level", "UNKNOWN"),
        "market": market,
        "factors": factors,
        "fetched_at": market.get("fetched_at"),
        "cache_status": cache_status,
    }
