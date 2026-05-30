"""
Network & Risk Report Tools for Vartovii ADK Agent.

Cross-entity analysis and comprehensive reporting:
- get_entity_network: Find connections between entities
- generate_risk_report: Comprehensive risk assessment with recommendations

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
# Mock data generators
# ---------------------------------------------------------------------------

def _name_hash(name: str) -> int:
    """Deterministic hash from entity name for consistent mock data."""
    return int(hashlib.md5(name.encode()).hexdigest(), 16)


def _mock_company_network(entity_name: str) -> dict:
    """Generate realistic company network connections."""
    h = _name_hash(entity_name)
    investor_pool = [
        "Sequoia Capital", "a16z", "SoftBank Vision Fund",
        "Tiger Global", "Accel Partners", "Benchmark",
        "Kleiner Perkins", "GV (Google Ventures)", "Insight Partners",
    ]
    board_pool = [
        "Dr. Sarah Mueller", "James Chen", "Maria Gonzalez",
        "Robert Fischer", "Aisha Patel", "Hans Weber",
        "Emily Rodriguez", "Thomas Schmidt", "Lisa Park",
    ]
    supply_chain = [
        "AWS", "Microsoft Azure", "Salesforce", "SAP",
        "Oracle", "Accenture", "Deloitte", "McKinsey",
        "TSMC", "Samsung Electronics",
    ]

    shared_investors = [investor_pool[(h + i) % len(investor_pool)] for i in range(2 + h % 3)]
    common_board = [board_pool[(h + i) % len(board_pool)] for i in range(1 + h % 2)]
    supply_links = [supply_chain[(h + i) % len(supply_chain)] for i in range(2 + h % 3)]

    return {
        "shared_investors": shared_investors,
        "common_board_members": common_board,
        "supply_chain_links": supply_links,
        "funding_relationships": [
            {
                "investor": shared_investors[0],
                "round": "Series " + chr(65 + h % 4),
                "amount_usd": 10_000_000 + (h % 200_000_000),
                "date": f"202{3 + h % 3}-0{1 + h % 9}-15",
            },
        ],
        "network_risk_score": round(20 + (h % 60), 1),
        "total_connections": len(shared_investors) + len(common_board) + len(supply_links),
    }


def _mock_crypto_network(entity_name: str) -> dict:
    """Generate realistic crypto project network connections."""
    h = _name_hash(entity_name)
    investor_pool = [
        "a16z", "Paradigm", "Multicoin Capital", "Polychain Capital",
        "Pantera Capital", "Dragonfly", "Framework Ventures",
        "Coinbase Ventures", "Binance Labs", "Jump Crypto",
    ]
    partner_pool = [
        "Chainlink", "The Graph", "Optimism", "Arbitrum",
        "Polygon", "Cosmos", "Filecoin", "Starkware",
    ]
    audit_pool = [
        "CertiK", "Trail of Bits", "OpenZeppelin",
        "Quantstamp", "Consensys Diligence",
    ]

    shared_investors = [investor_pool[(h + i) % len(investor_pool)] for i in range(3 + h % 3)]
    partnerships = [partner_pool[(h + i) % len(partner_pool)] for i in range(2 + h % 3)]
    shared_auditors = [audit_pool[(h + i) % len(audit_pool)] for i in range(1 + h % 2)]

    return {
        "shared_investors": shared_investors,
        "common_board_members": [],
        "technology_partnerships": partnerships,
        "shared_auditors": shared_auditors,
        "funding_relationships": [
            {
                "investor": shared_investors[0],
                "round": "Seed" if h % 3 == 0 else "Series A",
                "amount_usd": 5_000_000 + (h % 100_000_000),
                "date": f"202{2 + h % 4}-0{1 + h % 9}-20",
            },
        ],
        "network_risk_score": round(15 + (h % 65), 1),
        "total_connections": len(shared_investors) + len(partnerships) + len(shared_auditors),
    }


def _mock_risk_report(entity_name: str, entity_type: str) -> dict:
    """Generate a comprehensive mock risk report."""
    h = _name_hash(entity_name)
    trust_score = 30 + (h % 60)
    risk_level = (
        "LOW" if trust_score >= 80 else
        "MEDIUM" if trust_score >= 60 else
        "HIGH" if trust_score >= 40 else
        "CRITICAL"
    )

    risk_factors = []
    if trust_score < 50:
        risk_factors.append({"factor": "Low trust score", "severity": "HIGH", "detail": f"Score {trust_score}/100 is below acceptable threshold"})
    if h % 4 == 0:
        risk_factors.append({"factor": "Regulatory concerns", "severity": "MEDIUM", "detail": "Pending regulatory actions or investigations"})
    if h % 5 == 0:
        risk_factors.append({"factor": "Leadership instability", "severity": "MEDIUM", "detail": "Frequent executive turnover in last 12 months"})
    if h % 3 == 0:
        risk_factors.append({"factor": "Financial transparency", "severity": "LOW", "detail": "Limited public financial disclosures"})

    recommendations = []
    if trust_score < 60:
        recommendations.append("Conduct enhanced due diligence before engagement")
    if trust_score < 40:
        recommendations.append("Consider disengagement or risk mitigation measures")
    recommendations.append("Monitor entity for trust score changes quarterly")
    if entity_type == "crypto":
        recommendations.append("Verify smart contract audit status before investment")
    else:
        recommendations.append("Review recent employee sentiment trends")

    return {
        "entity_name": entity_name,
        "entity_type": entity_type,
        "report_date": "2026-05-30T12:00:00Z",
        "trust_score": trust_score,
        "risk_level": risk_level,
        "risk_summary": f"{entity_name} presents {'elevated' if trust_score < 60 else 'manageable'} risk based on available data.",
        "risk_factors": risk_factors,
        "trust_breakdown": {
            "data_quality": round(40 + (h % 50), 1),
            "reputation": round(30 + (h % 60), 1),
            "financial_health": round(35 + (h % 55), 1),
            "transparency": round(25 + (h % 65), 1),
        },
        "network_analysis": {
            "total_connections": 5 + (h % 15),
            "high_risk_connections": h % 3,
            "investor_overlap_with_flagged_entities": h % 2 == 0,
        },
        "recommendations": recommendations,
        "confidence_level": "HIGH" if h % 3 == 0 else "MEDIUM",
    }


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

def get_entity_network(entity_name: str, entity_type: str = "company") -> dict:
    """
    Map the relationship network of an entity — shared investors,
    board members, supply chain links, and funding relationships.

    Discovers hidden connections between entities that may indicate
    risk contagion or conflicts of interest.

    Args:
        entity_name: Name of the entity (e.g., "Google", "Uniswap")
        entity_type: Type of entity: "company" or "crypto" (default: "company")

    Returns:
        Shared investors, common board members, supply chain links,
        funding relationships, network risk score, total connections.
    """
    entity_type = entity_type.strip().lower()
    if entity_type not in ("company", "crypto"):
        return {"found": False, "message": f"Invalid entity_type '{entity_type}'. Must be 'company' or 'crypto'."}

    # Try MongoDB lookup between collections
    if is_mongodb_available():
        col_name = "companies" if entity_type == "company" else "crypto_projects"
        col = get_collection(col_name)
        if col is not None:
            try:
                search_field = "company_name" if entity_type == "company" else "name"
                result = col.find_one(
                    {search_field: {"$regex": entity_name.strip(), "$options": "i"}},
                    {"_id": 0},
                )
                if result:
                    # Try to find network data on the document
                    network_data = result.get("network_data")
                    if network_data:
                        return {
                            "found": True,
                            "entity_name": result.get(search_field, entity_name),
                            "entity_type": entity_type,
                            **network_data,
                            "source": "mongodb",
                        }

                    # Cross-collection lookup for shared investors
                    other_col_name = "crypto_projects" if entity_type == "company" else "companies"
                    other_col = get_collection(other_col_name)
                    if other_col is not None:
                        investors = result.get("lead_investors", [])
                        if investors:
                            investor_field = "lead_investors"
                            related = list(other_col.find(
                                {investor_field: {"$in": investors}},
                                {"_id": 0, "name": 1, "company_name": 1, "slug": 1, "profile_slug": 1},
                            ).limit(5))
                            if related:
                                logger.info(
                                    "🔗 Network: found %d cross-entity connections for '%s'",
                                    len(related), entity_name,
                                )
                                return {
                                    "found": True,
                                    "entity_name": result.get(search_field, entity_name),
                                    "entity_type": entity_type,
                                    "shared_investors": investors,
                                    "cross_entity_connections": related,
                                    "total_connections": len(related) + len(investors),
                                    "source": "mongodb",
                                }
            except Exception as e:
                logger.warning("MongoDB get_entity_network failed: %s", e)

    # Fallback to computed mock data
    if entity_type == "company":
        mock = _mock_company_network(entity_name)
    else:
        mock = _mock_crypto_network(entity_name)

    return {
        "found": True,
        "entity_name": entity_name,
        "entity_type": entity_type,
        **mock,
        "source": "mock",
    }


def generate_risk_report(entity_name: str, entity_type: str = "company") -> dict:
    """
    Generate a comprehensive risk report combining trust score,
    reviews, network analysis, and actionable recommendations.

    Produces a structured JSON report suitable for export or
    presentation to stakeholders.

    Args:
        entity_name: Name of the entity (e.g., "Wirecard", "FTX Token")
        entity_type: Type of entity: "company" or "crypto" (default: "company")

    Returns:
        Comprehensive risk report with trust score, risk level,
        risk factors, trust breakdown, network analysis,
        recommendations, and confidence level.
    """
    entity_type = entity_type.strip().lower()
    if entity_type not in ("company", "crypto"):
        return {"found": False, "message": f"Invalid entity_type '{entity_type}'. Must be 'company' or 'crypto'."}

    # Try MongoDB: combine data from multiple sources
    if is_mongodb_available():
        col_name = "companies" if entity_type == "company" else "crypto_projects"
        col = get_collection(col_name)
        if col is not None:
            try:
                search_field = "company_name" if entity_type == "company" else "name"
                slug_field = "profile_slug" if entity_type == "company" else "slug"
                key = entity_name.strip().lower().split()[0]

                result = col.find_one(
                    {"$or": [
                        {search_field: {"$regex": entity_name.strip(), "$options": "i"}},
                        {slug_field: {"$regex": f"^{key}", "$options": "i"}},
                    ]},
                    {"_id": 0},
                )

                if result:
                    trust_score = result.get("trust_score", 0)
                    risk_level = result.get("risk_level", "UNKNOWN")
                    name = result.get(search_field, entity_name)

                    # Get review sentiment if company
                    review_summary = None
                    if entity_type == "company":
                        reviews_col = get_collection("reviews")
                        if reviews_col is not None:
                            slug = result.get("profile_slug", "")
                            review_count = reviews_col.count_documents(
                                {"company_slug": slug}
                            )
                            review_summary = {
                                "total_reviews": review_count,
                                "avg_rating": result.get("avg_rating"),
                                "sentiment_positive_pct": result.get("sentiment_positive_pct"),
                            }

                    risk_factors = []
                    if trust_score < 50:
                        risk_factors.append({
                            "factor": "Low trust score",
                            "severity": "HIGH",
                            "detail": f"Score {trust_score}/100 below threshold",
                        })
                    if result.get("sentiment_negative_pct", 0) > 50:
                        risk_factors.append({
                            "factor": "Negative sentiment majority",
                            "severity": "HIGH",
                            "detail": f"{result['sentiment_negative_pct']}% negative reviews",
                        })

                    recommendations = []
                    if trust_score < 40:
                        recommendations.append("Immediate risk review recommended")
                    elif trust_score < 60:
                        recommendations.append("Enhanced monitoring advised")
                    else:
                        recommendations.append("Standard periodic review sufficient")
                    recommendations.append("Re-evaluate in 90 days")

                    report = {
                        "found": True,
                        "entity_name": name,
                        "entity_type": entity_type,
                        "report_date": "2026-05-30T12:00:00Z",
                        "trust_score": trust_score,
                        "risk_level": risk_level,
                        "risk_summary": (
                            f"{name} has a trust score of {trust_score}/100 "
                            f"with {risk_level} risk level."
                        ),
                        "score_breakdown": result.get("score_breakdown", {}),
                        "risk_factors": risk_factors,
                        "recommendations": recommendations,
                        "confidence_level": "HIGH",
                        "source": "mongodb",
                    }
                    if review_summary:
                        report["review_summary"] = review_summary
                    return report
            except Exception as e:
                logger.warning("MongoDB generate_risk_report failed: %s", e)

    # Fallback to computed mock data
    mock = _mock_risk_report(entity_name, entity_type)
    return {
        "found": True,
        **mock,
        "source": "mock",
    }
