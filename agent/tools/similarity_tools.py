"""
Similarity Search Tools for Vartovii ADK Agent.

Uses MongoDB aggregation pipelines to find entities with similar
risk profiles and trust characteristics. When a user investigates
Entity X, the agent can automatically surface similar entities
from the database — enabling pattern detection across the dataset.

In a production environment with MongoDB Atlas M10+, this would
use $vectorSearch with Gemini-generated embeddings. For the M0
free tier, we use a score-distance aggregation approach that is
equally effective for structured trust data.
"""

import logging
from typing import Optional

from .db import get_collection, is_mongodb_available

logger = logging.getLogger(__name__)


def find_similar_companies(
    company_name: str,
    limit: int = 5,
    risk_level_filter: Optional[str] = None,
) -> dict:
    """
    Find companies with similar trust profiles to a given company.

    Uses MongoDB aggregation to compute similarity based on trust score,
    sentiment, and risk characteristics. Useful for pattern detection:
    "Show me companies that look like Wirecard" → finds other potential frauds.

    Args:
        company_name: Reference company name to find similar ones
        limit: Max results (default: 5)
        risk_level_filter: Optional filter: "LOW", "MEDIUM", "HIGH", "CRITICAL"

    Returns:
        List of similar companies with similarity scores and risk analysis
    """
    if not is_mongodb_available():
        return {
            "found": False,
            "message": "MongoDB unavailable — similarity search requires database.",
            "similar": [],
        }

    companies_col = get_collection("companies")
    if companies_col is None:
        return {"found": False, "message": "Collection unavailable.", "similar": []}

    try:
        # Step 1: Get the reference company
        ref = companies_col.find_one(
            {"company_name": {"$regex": company_name.strip(), "$options": "i"}},
            {"_id": 0},
        )
        if not ref:
            # Try slug match
            key = company_name.strip().lower().split()[0]
            ref = companies_col.find_one(
                {"profile_slug": {"$regex": f"^{key}", "$options": "i"}},
                {"_id": 0},
            )

        if not ref:
            return {
                "found": False,
                "message": f"Reference company '{company_name}' not found.",
                "similar": [],
            }

        ref_score = ref["trust_score"]
        ref_sentiment = ref.get("sentiment_positive_pct", 50)

        # Step 2: Aggregation pipeline — compute distance from reference
        pipeline = [
            # Exclude the reference company itself
            {"$match": {"profile_slug": {"$ne": ref.get("profile_slug", "")}}},
        ]

        # Optional risk level filter
        if risk_level_filter:
            pipeline.append({"$match": {"risk_level": risk_level_filter.upper()}})

        pipeline.extend([
            # Compute similarity score (inverse of distance)
            {
                "$addFields": {
                    "score_distance": {
                        "$abs": {"$subtract": ["$trust_score", ref_score]}
                    },
                    "sentiment_distance": {
                        "$abs": {
                            "$subtract": [
                                {"$ifNull": ["$sentiment_positive_pct", 50]},
                                ref_sentiment,
                            ]
                        }
                    },
                }
            },
            # Combined similarity (lower = more similar)
            {
                "$addFields": {
                    "combined_distance": {
                        "$add": [
                            {"$multiply": ["$score_distance", 0.7]},
                            {"$multiply": ["$sentiment_distance", 0.3]},
                        ]
                    },
                    "similarity_pct": {
                        "$subtract": [
                            100,
                            {
                                "$min": [
                                    100,
                                    {
                                        "$add": [
                                            {"$multiply": ["$score_distance", 0.7]},
                                            {"$multiply": ["$sentiment_distance", 0.3]},
                                        ]
                                    },
                                ]
                            },
                        ]
                    },
                }
            },
            # Sort by similarity (lowest distance first)
            {"$sort": {"combined_distance": 1}},
            {"$limit": min(limit, 20)},
            # Project clean output
            {
                "$project": {
                    "_id": 0,
                    "company_name": 1,
                    "trust_score": 1,
                    "risk_level": 1,
                    "avg_rating": 1,
                    "review_count": 1,
                    "similarity_pct": {"$round": ["$similarity_pct", 1]},
                    "industry": 1,
                    "country": 1,
                }
            },
        ])

        results = list(companies_col.aggregate(pipeline))

        logger.info(
            "🔍 Similarity search: found %d companies similar to '%s'",
            len(results), company_name,
        )

        return {
            "found": True,
            "reference": {
                "company_name": ref["company_name"],
                "trust_score": ref_score,
                "risk_level": ref["risk_level"],
            },
            "similar_count": len(results),
            "similar": results,
            "message": (
                f"Found {len(results)} companies with similar trust profiles to "
                f"'{ref['company_name']}' (Trust Score: {ref_score})."
            ),
        }
    except Exception as e:
        logger.error("Similarity search failed: %s", e)
        return {"found": False, "message": f"Search failed: {e}", "similar": []}


def find_similar_crypto(
    project_slug: str,
    limit: int = 5,
    risk_level_filter: Optional[str] = None,
) -> dict:
    """
    Find crypto projects with similar risk and trust profiles.

    Compares trust score breakdown categories (treasury, dev_activity,
    security, financials, tokenomics, community) to find structurally
    similar projects. Useful for fraud pattern detection.

    Args:
        project_slug: Reference project slug (e.g., "bitcoin", "ftx")
        limit: Max results (default: 5)
        risk_level_filter: Optional filter: "LOW", "MEDIUM", "HIGH", "CRITICAL"

    Returns:
        List of similar crypto projects with similarity analysis
    """
    if not is_mongodb_available():
        return {
            "found": False,
            "message": "MongoDB unavailable.",
            "similar": [],
        }

    col = get_collection("crypto_projects")
    if col is None:
        return {"found": False, "message": "Collection unavailable.", "similar": []}

    try:
        # Step 1: Get reference project
        ref = col.find_one(
            {"slug": project_slug.strip().lower()},
            {"_id": 0},
        )
        if not ref:
            return {
                "found": False,
                "message": f"Reference project '{project_slug}' not found.",
                "similar": [],
            }

        ref_score = ref["trust_score"]
        ref_breakdown = ref.get("score_breakdown", {})

        # Step 2: Aggregation — multi-dimensional distance
        pipeline = [
            {"$match": {"slug": {"$ne": ref["slug"]}}},
        ]

        if risk_level_filter:
            pipeline.append({"$match": {"risk_level": risk_level_filter.upper()}})

        # Compute distance across all breakdown dimensions
        breakdown_fields = ["treasury", "dev_activity", "security", "financials", "tokenomics", "community"]
        distance_components = []
        for field in breakdown_fields:
            ref_val = ref_breakdown.get(field, 10)
            distance_components.append({
                "$abs": {
                    "$subtract": [
                        {"$ifNull": [f"$score_breakdown.{field}", 10]},
                        ref_val,
                    ]
                }
            })

        pipeline.extend([
            {
                "$addFields": {
                    "score_distance": {
                        "$abs": {"$subtract": ["$trust_score", ref_score]}
                    },
                    "breakdown_distance": {
                        "$avg": distance_components
                    },
                }
            },
            {
                "$addFields": {
                    "combined_distance": {
                        "$add": [
                            {"$multiply": ["$score_distance", 0.5]},
                            {"$multiply": ["$breakdown_distance", 2.5]},
                        ]
                    },
                    "similarity_pct": {
                        "$max": [
                            0,
                            {
                                "$subtract": [
                                    100,
                                    {
                                        "$add": [
                                            {"$multiply": ["$score_distance", 0.5]},
                                            {"$multiply": ["$breakdown_distance", 2.5]},
                                        ]
                                    },
                                ]
                            },
                        ]
                    },
                }
            },
            {"$sort": {"combined_distance": 1}},
            {"$limit": min(limit, 20)},
            {
                "$project": {
                    "_id": 0,
                    "name": 1,
                    "symbol": 1,
                    "slug": 1,
                    "trust_score": 1,
                    "risk_level": 1,
                    "similarity_pct": {"$round": ["$similarity_pct", 1]},
                    "score_breakdown": 1,
                }
            },
        ])

        results = list(col.aggregate(pipeline))

        logger.info(
            "🔍 Crypto similarity: found %d projects similar to '%s'",
            len(results), project_slug,
        )

        return {
            "found": True,
            "reference": {
                "name": ref["name"],
                "symbol": ref["symbol"],
                "trust_score": ref_score,
                "risk_level": ref["risk_level"],
            },
            "similar_count": len(results),
            "similar": results,
            "message": (
                f"Found {len(results)} crypto projects with similar profiles to "
                f"'{ref['name']}' ({ref['symbol']}, Score: {ref_score})."
            ),
        }
    except Exception as e:
        logger.error("Crypto similarity search failed: %s", e)
        return {"found": False, "message": f"Search failed: {e}", "similar": []}


def cross_entity_risk_scan(risk_level: str = "CRITICAL", limit: int = 10) -> dict:
    """
    Scan across ALL entity types for high-risk items.

    Performs a cross-collection risk assessment by querying both companies
    and crypto projects, combining results into a unified risk report.
    Essential for portfolio-wide fraud detection.

    Args:
        risk_level: Risk level to scan for: "CRITICAL", "HIGH", "MEDIUM", "LOW"
        limit: Max results per entity type (default: 10)

    Returns:
        Combined risk report across companies and crypto projects
    """
    if not is_mongodb_available():
        return {"found": False, "message": "MongoDB unavailable.", "entities": []}

    entities = []

    try:
        # Scan companies
        companies_col = get_collection("companies")
        if companies_col is not None:
            pipeline = [
                {"$match": {"risk_level": risk_level.upper()}},
                {"$sort": {"trust_score": 1}},
                {"$limit": limit},
                {
                    "$project": {
                        "_id": 0,
                        "entity_type": {"$literal": "company"},
                        "name": "$company_name",
                        "trust_score": 1,
                        "risk_level": 1,
                        "avg_rating": 1,
                        "industry": 1,
                    }
                },
            ]
            entities.extend(list(companies_col.aggregate(pipeline)))

        # Scan crypto projects
        crypto_col = get_collection("crypto_projects")
        if crypto_col is not None:
            pipeline = [
                {"$match": {"risk_level": risk_level.upper()}},
                {"$sort": {"trust_score": 1}},
                {"$limit": limit},
                {
                    "$project": {
                        "_id": 0,
                        "entity_type": {"$literal": "crypto"},
                        "name": 1,
                        "symbol": 1,
                        "trust_score": 1,
                        "risk_level": 1,
                    }
                },
            ]
            entities.extend(list(crypto_col.aggregate(pipeline)))

        # Sort combined by trust_score ascending (worst first)
        entities.sort(key=lambda x: x.get("trust_score", 0))

        logger.info(
            "🚨 Cross-entity risk scan: found %d %s-risk entities",
            len(entities), risk_level,
        )

        return {
            "found": bool(entities),
            "risk_level": risk_level,
            "total_flagged": len(entities),
            "entities": entities,
            "message": (
                f"Found {len(entities)} entities with {risk_level} risk level "
                f"across companies and crypto projects."
            ),
        }
    except Exception as e:
        logger.error("Cross-entity risk scan failed: %s", e)
        return {"found": False, "message": f"Scan failed: {e}", "entities": []}
