"""
Advanced Corporate Tools for Vartovii ADK Agent.

Extended analytics tools for deeper corporate intelligence:
- get_salary_insights: Salary ranges, medians, industry comparison
- get_hiring_trends: Hiring velocity, remote ratio, diversity metrics
- get_industry_benchmark: Industry-wide aggregation and comparison

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
# Mock data generators — deterministic, entity-name-based
# ---------------------------------------------------------------------------

def _name_hash(name: str) -> int:
    """Deterministic hash from entity name for consistent mock data."""
    return int(hashlib.md5(name.encode()).hexdigest(), 16)


def _mock_salary_data(company_name: str) -> dict:
    """Generate realistic salary data based on company name."""
    h = _name_hash(company_name)
    base = 55000 + (h % 45000)  # 55k–100k range for junior
    return {
        "salary_ranges": {
            "junior": {"min": base, "max": base + 15000, "currency": "EUR"},
            "mid": {"min": base + 20000, "max": base + 40000, "currency": "EUR"},
            "senior": {"min": base + 45000, "max": base + 75000, "currency": "EUR"},
        },
        "median_salary": base + 30000,
        "salary_vs_industry_avg_pct": round(-10 + (h % 30), 1),
        "benefits_summary": {
            "health_insurance": True,
            "remote_work": h % 3 != 0,
            "stock_options": h % 2 == 0,
            "pension_plan": True,
            "bonus_structure": "annual" if h % 2 == 0 else "quarterly",
            "vacation_days": 25 + (h % 10),
        },
    }


def _mock_hiring_data(company_name: str) -> dict:
    """Generate realistic hiring data based on company name."""
    h = _name_hash(company_name)
    open_positions = 50 + (h % 450)
    return {
        "open_positions": open_positions,
        "growth_rate_pct": round(-5.0 + (h % 25), 1),
        "trending_roles": _pick_roles(h),
        "remote_vs_office": {
            "remote_pct": round(15 + (h % 55), 1),
            "hybrid_pct": round(20 + (h % 30), 1),
            "office_pct": round(100 - (15 + (h % 55)) - (20 + (h % 30)), 1),
        },
        "diversity_score": round(40 + (h % 50), 1),
        "avg_time_to_hire_days": 20 + (h % 40),
    }


def _pick_roles(h: int) -> list[str]:
    """Pick trending roles based on hash value."""
    all_roles = [
        "Software Engineer", "Data Scientist", "Product Manager",
        "DevOps Engineer", "Machine Learning Engineer", "UX Designer",
        "Cloud Architect", "Security Engineer", "Full-Stack Developer",
        "Engineering Manager",
    ]
    start = h % 5
    return all_roles[start:start + 4]


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

def get_salary_insights(company_name: str) -> dict:
    """
    Get salary intelligence for a company — ranges by seniority,
    median salary, industry comparison, and benefits overview.

    Args:
        company_name: Name of the company (e.g., "Google", "SAP", "BMW")

    Returns:
        Salary ranges (junior/mid/senior), median salary, salary vs
        industry average percentage, and benefits summary.
    """
    key = company_name.strip().lower().split()[0] if company_name else ""

    # Try MongoDB first
    if is_mongodb_available():
        col = get_collection("companies")
        if col is not None:
            try:
                result = col.find_one(
                    {"$or": [
                        {"profile_slug": {"$regex": f"^{key}", "$options": "i"}},
                        {"company_name": {"$regex": company_name.strip(), "$options": "i"}},
                    ]},
                    {"_id": 0, "company_name": 1, "salary_data": 1},
                )
                if result and result.get("salary_data"):
                    return {
                        "found": True,
                        "company_name": result.get("company_name", company_name),
                        **result["salary_data"],
                        "source": "mongodb",
                    }
            except Exception as e:
                logger.warning("MongoDB get_salary_insights failed: %s", e)

    # Fallback to computed mock data
    mock = _mock_salary_data(company_name)
    return {
        "found": True,
        "company_name": company_name,
        **mock,
        "source": "mock",
    }


def get_hiring_trends(company_name: str) -> dict:
    """
    Get hiring trend intelligence for a company — open positions,
    growth rate, trending roles, remote vs office ratio, diversity score.

    Args:
        company_name: Name of the company (e.g., "Google", "SAP", "BMW")

    Returns:
        Open positions count, growth rate %, trending roles list,
        remote/hybrid/office ratio, diversity score, avg time to hire.
    """
    key = company_name.strip().lower().split()[0] if company_name else ""

    # Try MongoDB first
    if is_mongodb_available():
        col = get_collection("companies")
        if col is not None:
            try:
                result = col.find_one(
                    {"$or": [
                        {"profile_slug": {"$regex": f"^{key}", "$options": "i"}},
                        {"company_name": {"$regex": company_name.strip(), "$options": "i"}},
                    ]},
                    {"_id": 0, "company_name": 1, "hiring_data": 1},
                )
                if result and result.get("hiring_data"):
                    return {
                        "found": True,
                        "company_name": result.get("company_name", company_name),
                        **result["hiring_data"],
                        "source": "mongodb",
                    }
            except Exception as e:
                logger.warning("MongoDB get_hiring_trends failed: %s", e)

    # Fallback to computed mock data
    mock = _mock_hiring_data(company_name)
    return {
        "found": True,
        "company_name": company_name,
        **mock,
        "source": "mock",
    }


def get_industry_benchmark(industry: str) -> dict:
    """
    Benchmark companies within the same industry — average trust score,
    top/worst performers, average rating, total employee count.

    Uses MongoDB aggregation pipeline to group companies by industry.

    Args:
        industry: Industry name or keyword (e.g., "Technology", "Automotive",
                  "Fintech"). Partial matches are supported.

    Returns:
        Industry benchmark with avg trust score, top performer,
        worst performer, avg rating, total employees, and company count.
    """
    # Try MongoDB aggregation first
    if is_mongodb_available():
        col = get_collection("companies")
        if col is not None:
            try:
                pipeline = [
                    {"$match": {"industry": {"$regex": industry.strip(), "$options": "i"}}},
                    {"$sort": {"trust_score": -1}},
                    {
                        "$group": {
                            "_id": None,
                            "avg_trust_score": {"$avg": "$trust_score"},
                            "avg_rating": {"$avg": "$avg_rating"},
                            "total_employees": {"$sum": "$employee_count"},
                            "company_count": {"$sum": 1},
                            "top_performer": {"$first": "$company_name"},
                            "top_score": {"$first": "$trust_score"},
                            "worst_performer": {"$last": "$company_name"},
                            "worst_score": {"$last": "$trust_score"},
                            "companies": {
                                "$push": {
                                    "name": "$company_name",
                                    "trust_score": "$trust_score",
                                    "risk_level": "$risk_level",
                                }
                            },
                        }
                    },
                ]

                results = list(col.aggregate(pipeline))
                if results:
                    data = results[0]
                    return {
                        "found": True,
                        "industry": industry,
                        "avg_trust_score": round(data["avg_trust_score"], 1),
                        "avg_rating": round(data["avg_rating"], 2),
                        "total_employees": data["total_employees"],
                        "company_count": data["company_count"],
                        "top_performer": {
                            "name": data["top_performer"],
                            "trust_score": data["top_score"],
                        },
                        "worst_performer": {
                            "name": data["worst_performer"],
                            "trust_score": data["worst_score"],
                        },
                        "companies": data["companies"],
                        "source": "mongodb",
                    }
            except Exception as e:
                logger.warning("MongoDB get_industry_benchmark failed: %s", e)

    # Fallback: mock benchmark data
    h = _name_hash(industry)
    return {
        "found": True,
        "industry": industry,
        "avg_trust_score": round(55 + (h % 30), 1),
        "avg_rating": round(3.2 + (h % 15) / 10, 2),
        "total_employees": 50000 + (h % 500000),
        "company_count": 3 + (h % 8),
        "top_performer": {
            "name": f"Top {industry} Corp",
            "trust_score": 80 + (h % 15),
        },
        "worst_performer": {
            "name": f"Lagging {industry} Inc",
            "trust_score": 25 + (h % 30),
        },
        "companies": [],
        "source": "mock",
    }
