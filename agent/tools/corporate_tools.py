"""
Corporate Tools for Vartovii ADK Agent.

All tools for the Corporate Intelligence sub-agent:
- search_company: Find a company in the database
- get_trust_score: Get Trust Score breakdown
- list_companies: Top employers ranking
- compare_companies: Side-by-side comparison
- get_company_reviews: Employee review samples
- get_vacancy_intelligence: Ghost jobs, time-to-fill, hiring velocity

In production, these query PostgreSQL with 500+ companies and 100K+ reviews.
For the submission demo, they use mock data providers.
"""

import logging
from typing import Optional

from .mock_data import COMPANIES, REVIEWS, VACANCIES

logger = logging.getLogger(__name__)


def search_company(company_name: str, country: Optional[str] = None) -> dict:
    """
    Search for a company in the Vartovii database.

    Args:
        company_name: Name of the company to search for (e.g., "BMW", "Lidl", "SAP")
        country: Optional country code to filter by (de, at, ch)

    Returns:
        Company info with trust_score, avg_rating, review_count, sentiment
    """
    key = company_name.strip().lower().split()[0] if company_name else ""
    company = COMPANIES.get(key)

    if not company:
        return {
            "found": False,
            "message": (
                f"Company '{company_name}' not found in database. "
                "User can use Magic Search on the website to add it."
            ),
        }

    return {"found": True, **company}


def get_trust_score(company_name: str) -> dict:
    """
    Get detailed Trust Score breakdown for a company.

    Args:
        company_name: Name of the company to get Trust Score for

    Returns:
        Trust score with risk level and breakdown by categories
    """
    key = company_name.strip().lower().split()[0] if company_name else ""
    company = COMPANIES.get(key)

    if not company:
        return {"error": f"Company '{company_name}' not found in database."}

    return {
        "company_name": company["company_name"],
        "trust_score": company["trust_score"],
        "risk_level": company["risk_level"],
        "avg_rating": company["avg_rating"],
        "review_count": company["review_count"],
        "breakdown": company["score_breakdown"],
    }


def list_companies(
    country: Optional[str] = None, limit: int = 10, sort_by: str = "trust_score"
) -> dict:
    """
    Get a list of top employers sorted by Trust Score or other metrics.

    Args:
        country: Optional country code (de, at, ch) to filter by
        limit: Number of companies to return (default: 10, max: 50)
        sort_by: Sort by "trust_score", "review_count", or "avg_rating"

    Returns:
        List of companies with trust scores and ratings
    """
    results = [
        {
            "company_name": c["company_name"],
            "trust_score": c["trust_score"],
            "risk_level": c["risk_level"],
            "avg_rating": c["avg_rating"],
            "review_count": c["review_count"],
        }
        for c in COMPANIES.values()
    ]

    sort_key = sort_by if sort_by in ("trust_score", "review_count", "avg_rating") else "trust_score"
    results.sort(key=lambda x: x[sort_key], reverse=True)
    results = results[: min(limit, 50)]

    return {"companies": results, "count": len(results)}


def compare_companies(company1: str, company2: str) -> dict:
    """
    Compare two companies side-by-side on Trust Score, ratings, and sentiment.

    Args:
        company1: First company name (e.g., "BMW")
        company2: Second company name (e.g., "SAP")

    Returns:
        Comparison with winner recommendation
    """
    if not company1 or not company2:
        return {"error": "Both company1 and company2 are required"}

    c1 = search_company(company1)
    c2 = search_company(company2)

    if not c1.get("found"):
        return {"error": f"Company '{company1}' not found"}
    if not c2.get("found"):
        return {"error": f"Company '{company2}' not found"}

    s1, s2 = c1["trust_score"], c2["trust_score"]

    if s1 > s2:
        winner, reason = c1["company_name"], f"Higher Trust Score ({s1} vs {s2})"
    elif s2 > s1:
        winner, reason = c2["company_name"], f"Higher Trust Score ({s2} vs {s1})"
    else:
        winner, reason = "Tie", "Both companies have equal scores"

    return {
        "company1": {
            "name": c1["company_name"],
            "trust_score": s1,
            "risk_level": c1["risk_level"],
            "avg_rating": c1["avg_rating"],
            "review_count": c1["review_count"],
        },
        "company2": {
            "name": c2["company_name"],
            "trust_score": s2,
            "risk_level": c2["risk_level"],
            "avg_rating": c2["avg_rating"],
            "review_count": c2["review_count"],
        },
        "winner": winner,
        "winner_reason": reason,
    }


def get_company_reviews(
    company_name: str, sentiment_filter: str = "all", limit: int = 5
) -> dict:
    """
    Get recent employee reviews for a company.

    Args:
        company_name: Company name to get reviews for
        sentiment_filter: Filter by "positive", "negative", or "all"
        limit: Max reviews to return (default: 5, max: 10)

    Returns:
        Sample reviews with sentiment and source info
    """
    key = company_name.strip().lower().split()[0] if company_name else ""
    reviews = REVIEWS.get(key, [])

    if sentiment_filter != "all":
        reviews = [r for r in reviews if r["sentiment"].lower() == sentiment_filter.lower()]

    return {
        "company_name": company_name,
        "reviews": reviews[: min(limit, 10)],
        "count": len(reviews),
    }


def get_vacancy_intelligence(company_name: str) -> dict:
    """
    Get vacancy intelligence for a company: ghost jobs, hiring velocity, time-to-fill.

    Args:
        company_name: Company name or slug to analyze

    Returns:
        Vacancy metrics: ghost_jobs, avg_time_to_fill, hiring_velocity, total_vacancies
    """
    key = company_name.strip().lower().split()[0] if company_name else ""
    data = VACANCIES.get(key)

    if not data:
        return {"found": False, "message": f"No vacancy data for '{company_name}'"}

    return {"found": True, "company_name": company_name, **data}
