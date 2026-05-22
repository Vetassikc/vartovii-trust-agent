"""
Mock data providers for the submission demo.

These replace live database queries with realistic sample data so the
agent architecture can be demonstrated without requiring a production
database connection. In the production Vartovii platform, these are
backed by PostgreSQL, CoinGecko, Etherscan, and other live APIs.
"""

# ============================================
# Corporate Mock Data
# ============================================

COMPANIES = {
    "sap": {
        "company_name": "SAP",
        "profile_slug": "sap-se",
        "trust_score": 74,
        "risk_level": "MEDIUM",
        "avg_rating": 3.85,
        "review_count": 1247,
        "sentiment_positive_pct": 68.2,
        "sentiment_negative_pct": 31.8,
        "score_breakdown": {
            "base_rating": 38.5,
            "volume_bonus": 15.0,
            "sentiment_bonus": 9.1,
            "source_diversity_bonus": 6.0,
            "recency_bonus": 3.5,
            "consistency_bonus": 1.9,
        },
        "data_freshness": "2026-05-20T14:30:00Z",
    },
    "bmw": {
        "company_name": "BMW Group",
        "profile_slug": "bmw-group",
        "trust_score": 82,
        "risk_level": "LOW",
        "avg_rating": 4.12,
        "review_count": 892,
        "sentiment_positive_pct": 76.4,
        "sentiment_negative_pct": 23.6,
        "score_breakdown": {
            "base_rating": 41.2,
            "volume_bonus": 14.0,
            "sentiment_bonus": 13.2,
            "source_diversity_bonus": 6.0,
            "recency_bonus": 4.2,
            "consistency_bonus": 3.4,
        },
        "data_freshness": "2026-05-19T09:15:00Z",
    },
    "wirecard": {
        "company_name": "Wirecard AG",
        "profile_slug": "wirecard-ag",
        "trust_score": 28,
        "risk_level": "CRITICAL",
        "avg_rating": 2.10,
        "review_count": 156,
        "sentiment_positive_pct": 22.1,
        "sentiment_negative_pct": 77.9,
        "score_breakdown": {
            "base_rating": 14.0,
            "volume_bonus": 6.0,
            "sentiment_bonus": 0.0,
            "source_diversity_bonus": 4.0,
            "recency_bonus": 0.0,
            "consistency_bonus": 4.0,
        },
        "data_freshness": "2026-05-18T11:00:00Z",
    },
}

REVIEWS = {
    "sap": [
        {
            "source": "kununu",
            "rating": 4.0,
            "title": "Good work-life balance, slow decision making",
            "sentiment": "POSITIVE",
            "date": "2026-04-15",
        },
        {
            "source": "glassdoor",
            "rating": 3.5,
            "title": "Stable but bureaucratic",
            "sentiment": "NEUTRAL",
            "date": "2026-03-28",
        },
        {
            "source": "google",
            "rating": 4.2,
            "title": "Great benefits and international culture",
            "sentiment": "POSITIVE",
            "date": "2026-05-01",
        },
    ],
}

VACANCIES = {
    "sap": {
        "total_vacancies": 342,
        "active_vacancies": 287,
        "closed_vacancies": 55,
        "ghost_jobs": 12,
        "avg_time_to_fill_days": 34.7,
    },
}

# ============================================
# Crypto Mock Data
# ============================================

CRYPTO_PROJECTS = {
    "bitcoin": {
        "slug": "bitcoin",
        "name": "Bitcoin",
        "symbol": "BTC",
        "price_usd": 68432.15,
        "market_cap": 1347000000000,
        "trust_score": 92,
        "risk_level": "LOW",
        "score_breakdown": {
            "treasury": 19,
            "dev_activity": 17,
            "security": 20,
            "financials": 14,
            "tokenomics": 13,
            "community": 9,
        },
        "project_stage": "live-token",
        "has_token": True,
        "github_org": "bitcoin",
        "commits_last_30d": 87,
        "active_devs": 34,
        "tvl": None,
        "total_raised": None,
        "certik_score": None,
        "tweetscout_score": 95,
    },
    "ethereum": {
        "slug": "ethereum",
        "name": "Ethereum",
        "symbol": "ETH",
        "price_usd": 3847.22,
        "market_cap": 462000000000,
        "trust_score": 94,
        "risk_level": "LOW",
        "score_breakdown": {
            "treasury": 20,
            "dev_activity": 19,
            "security": 20,
            "financials": 14,
            "tokenomics": 12,
            "community": 9,
        },
        "project_stage": "live-token",
        "has_token": True,
        "github_org": "ethereum",
        "commits_last_30d": 214,
        "active_devs": 89,
        "tvl": 58700000000,
        "total_raised": None,
        "certik_score": None,
        "tweetscout_score": 98,
    },
    "uniswap": {
        "slug": "uniswap",
        "name": "Uniswap",
        "symbol": "UNI",
        "price_usd": 11.84,
        "market_cap": 7100000000,
        "trust_score": 78,
        "risk_level": "MEDIUM",
        "score_breakdown": {
            "treasury": 16,
            "dev_activity": 18,
            "security": 16,
            "financials": 12,
            "tokenomics": 8,
            "community": 8,
        },
        "project_stage": "live-token",
        "has_token": True,
        "github_org": "Uniswap",
        "commits_last_30d": 156,
        "active_devs": 42,
        "tvl": 5200000000,
        "total_raised": 176000000,
        "lead_investors": ["a16z", "Paradigm"],
        "certik_score": 89,
        "tweetscout_score": 82,
    },
}

WALLETS = {
    "0xd8da6bf26964af9d7eed9e03e53415d37aa96045": {
        "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        "eth_balance": 1247.83,
        "usd_value": 4802431.67,
        "label": "vitalik.eth",
    },
}
