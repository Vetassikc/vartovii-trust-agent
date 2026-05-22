"""
Crypto & Forensic Tools for Vartovii ADK Agent.

All tools for the Crypto Intelligence sub-agent:
- search_crypto_projects: Search crypto projects in DB + CoinGecko
- get_crypto_trust_score: Full project data with Trust Score breakdown
- check_wallet: ETH balance for any address
- get_transaction_history: Recent transactions for an address
- get_token_holders: Top holders of an ERC20 token
- get_contract_info: Smart contract verification info

In production, these query PostgreSQL (6700+ crypto projects),
CoinGecko (live market data), and Etherscan (on-chain forensics).
For the submission demo, they use mock data providers.
"""

import logging

from .mock_data import CRYPTO_PROJECTS, WALLETS

logger = logging.getLogger(__name__)


def search_crypto_projects(query: str) -> dict:
    """
    Search for a cryptocurrency project/token by name, symbol or slug.

    Args:
        query: Project name, symbol or slug (e.g. "BTC", "Ethereum", "Uniswap")

    Returns:
        Matching projects with price, market cap, trust score
    """
    query_lower = query.strip().lower()
    results = []

    for slug, project in CRYPTO_PROJECTS.items():
        if (
            query_lower in slug
            or query_lower in project["name"].lower()
            or query_lower in project["symbol"].lower()
        ):
            results.append({
                "slug": project["slug"],
                "name": project["name"],
                "symbol": project["symbol"],
                "price_usd": project["price_usd"],
                "market_cap": project["market_cap"],
                "trust_score": project["trust_score"],
                "risk_level": project["risk_level"],
            })

    if not results:
        return {
            "found": False,
            "message": (
                f"Project '{query}' not found in local database. "
                "Use Google Search to analyze it via web research."
            ),
        }

    return {
        "found": True,
        "count": len(results),
        "results": results,
        "message": f"Found {len(results)} projects matching '{query}'.",
    }


def get_crypto_trust_score(slug: str) -> dict:
    """
    Get full crypto project data including Trust Score, tokenomics, investors, TVL.

    Args:
        slug: Project slug from search results (e.g. "bitcoin", "uniswap")

    Returns:
        Comprehensive project data with trust score breakdown, funding info,
        dev activity, treasury, and security scores
    """
    project = CRYPTO_PROJECTS.get(slug.strip().lower())

    if not project:
        return {"found": False, "message": f"Project '{slug}' not found. Try searching first."}

    return {
        "found": True,
        **project,
        "ai_hint": "Use these REAL numbers in your response. Don't say 'if' — state the actual data.",
    }


# ========== Forensic Tools ==========


def check_wallet(address: str) -> dict:
    """
    Check ETH balance for any Ethereum wallet address.

    Args:
        address: Ethereum address starting with 0x

    Returns:
        ETH balance, USD value, Etherscan link
    """
    if not address.startswith("0x"):
        return {"error": "Invalid address format. Must start with 0x"}

    wallet = WALLETS.get(address.lower())
    if wallet:
        return {
            "address": wallet["address"],
            "eth_balance": wallet["eth_balance"],
            "usd_value": wallet["usd_value"],
            "found": True,
            "chain": "ethereum",
            "label": wallet.get("label"),
            "etherscan_link": f"https://etherscan.io/address/{address}",
            "message": (
                f"Wallet {address[:10]}... holds {wallet['eth_balance']:.4f} ETH "
                f"≈ ${wallet['usd_value']:,.2f} USD"
            ),
        }

    # Demo: return a generic response for unknown wallets
    return {
        "address": address,
        "eth_balance": 0.0,
        "usd_value": 0.0,
        "found": True,
        "chain": "ethereum",
        "etherscan_link": f"https://etherscan.io/address/{address}",
        "message": f"Wallet {address[:10]}... — balance check complete.",
    }


def get_transaction_history(address: str, limit: int = 10, days: int = 30) -> dict:
    """
    Get recent transaction history for an Ethereum address.

    Args:
        address: Ethereum address (0x...)
        limit: Max transactions to return (default: 10)
        days: Look back this many days (default: 30)

    Returns:
        List of transactions with ETH value, direction, Etherscan links
    """
    if not address.startswith("0x"):
        return {"error": "Invalid address format"}

    # Demo: return sample transactions
    sample_txs = [
        {
            "tx_hash": "0xabc123...def456",
            "from": address,
            "to": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
            "value_eth": 1.5,
            "direction": "OUT",
            "timestamp": "2026-05-20T14:30:00Z",
            "etherscan_link": "https://etherscan.io/tx/0xabc123",
        },
        {
            "tx_hash": "0x789abc...012def",
            "from": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "to": address,
            "value_eth": 5.0,
            "direction": "IN",
            "timestamp": "2026-05-19T09:15:00Z",
            "etherscan_link": "https://etherscan.io/tx/0x789abc",
        },
    ]

    return {
        "address": address,
        "transactions": sample_txs[:limit],
        "count": len(sample_txs[:limit]),
        "etherscan_link": f"https://etherscan.io/address/{address}#transactions",
    }


def get_token_holders(contract_address: str, limit: int = 20) -> dict:
    """
    Get top holders of an ERC20 token to analyze concentration risk.

    Args:
        contract_address: ERC20 token contract address (0x...)
        limit: Max holders to return (default: 20)

    Returns:
        Top holders with balances and concentration metrics
    """
    if not contract_address.startswith("0x"):
        return {"error": "Invalid contract address"}

    # Demo: return sample holder distribution
    return {
        "contract_address": contract_address,
        "total_supply": 1000000000,
        "holders_count": 142857,
        "top_holders": [
            {"rank": 1, "address": "0x47ac0...Treasury", "balance_pct": 18.5, "label": "Treasury"},
            {"rank": 2, "address": "0x1f98...LP Pool", "balance_pct": 12.3, "label": "Uniswap V3 Pool"},
            {"rank": 3, "address": "0xBE0e...Binance", "balance_pct": 8.7, "label": "Binance Hot Wallet"},
        ],
        "concentration_top10_pct": 54.2,
        "concentration_risk": "MEDIUM",
    }


def get_contract_info(contract_address: str) -> dict:
    """
    Get information about a smart contract — type, deployment date, verification.

    Args:
        contract_address: Smart contract address (0x...)

    Returns:
        Contract type (ERC20/ERC721), deployment info, verification status
    """
    if not contract_address.startswith("0x"):
        return {"error": "Invalid contract address"}

    return {
        "address": contract_address,
        "contract_type": "ERC20",
        "is_verified": True,
        "compiler_version": "v0.8.19+commit.7dd6d404",
        "optimization_enabled": True,
        "license": "MIT",
        "etherscan_link": f"https://etherscan.io/address/{contract_address}#code",
    }
