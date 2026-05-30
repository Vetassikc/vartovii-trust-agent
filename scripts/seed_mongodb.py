#!/usr/bin/env python3
"""
Vartovii Trust Agent — MongoDB Atlas Seed Script

Populates the `vartovii` database with rich, realistic demo data for
the Google Cloud Rapid Agent Hackathon (MongoDB track).

Usage:
    python scripts/seed_mongodb.py           # seed (fails if collections exist)
    python scripts/seed_mongodb.py --force   # drop existing collections first

Environment:
    MONGODB_CONNECTION_STRING  — MongoDB Atlas connection URI (from .env)
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

import os

from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import ConnectionFailure, OperationFailure

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("seed_mongodb")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DATABASE_NAME = "vartovii"


# ═══════════════════════════════════════════════════════════════════════════
# DATA — Companies
# ═══════════════════════════════════════════════════════════════════════════

def _risk(score: int) -> str:
    """Derive risk level from trust score."""
    if score >= 80:
        return "LOW"
    if score >= 60:
        return "MEDIUM"
    if score >= 40:
        return "HIGH"
    return "CRITICAL"


COMPANIES: list[dict] = [
    {
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
        "country": "Germany",
        "industry": "Enterprise Software",
        "founded_year": 1972,
        "employee_count": 107000,
        "headquarters": "Walldorf, Germany",
    },
    {
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
        "country": "Germany",
        "industry": "Automotive",
        "founded_year": 1916,
        "employee_count": 149000,
        "headquarters": "Munich, Germany",
    },
    {
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
        "country": "Germany",
        "industry": "Fintech / Payments",
        "founded_year": 1999,
        "employee_count": 0,
        "headquarters": "Aschheim, Germany",
    },
    {
        "company_name": "Google",
        "profile_slug": "google-llc",
        "trust_score": 91,
        "risk_level": "LOW",
        "avg_rating": 4.50,
        "review_count": 4821,
        "sentiment_positive_pct": 84.3,
        "sentiment_negative_pct": 15.7,
        "score_breakdown": {
            "base_rating": 45.0,
            "volume_bonus": 15.0,
            "sentiment_bonus": 14.8,
            "source_diversity_bonus": 6.0,
            "recency_bonus": 5.0,
            "consistency_bonus": 5.2,
        },
        "data_freshness": "2026-05-28T08:00:00Z",
        "country": "United States",
        "industry": "Technology",
        "founded_year": 1998,
        "employee_count": 182000,
        "headquarters": "Mountain View, CA, USA",
    },
    {
        "company_name": "Apple",
        "profile_slug": "apple-inc",
        "trust_score": 88,
        "risk_level": "LOW",
        "avg_rating": 4.35,
        "review_count": 3956,
        "sentiment_positive_pct": 81.7,
        "sentiment_negative_pct": 18.3,
        "score_breakdown": {
            "base_rating": 43.5,
            "volume_bonus": 15.0,
            "sentiment_bonus": 13.5,
            "source_diversity_bonus": 6.0,
            "recency_bonus": 5.0,
            "consistency_bonus": 5.0,
        },
        "data_freshness": "2026-05-27T16:45:00Z",
        "country": "United States",
        "industry": "Technology / Consumer Electronics",
        "founded_year": 1976,
        "employee_count": 164000,
        "headquarters": "Cupertino, CA, USA",
    },
    {
        "company_name": "Meta Platforms",
        "profile_slug": "meta-platforms",
        "trust_score": 65,
        "risk_level": "MEDIUM",
        "avg_rating": 3.60,
        "review_count": 2134,
        "sentiment_positive_pct": 58.9,
        "sentiment_negative_pct": 41.1,
        "score_breakdown": {
            "base_rating": 36.0,
            "volume_bonus": 15.0,
            "sentiment_bonus": 5.9,
            "source_diversity_bonus": 5.0,
            "recency_bonus": 2.0,
            "consistency_bonus": 1.1,
        },
        "data_freshness": "2026-05-26T10:30:00Z",
        "country": "United States",
        "industry": "Social Media / Technology",
        "founded_year": 2004,
        "employee_count": 67000,
        "headquarters": "Menlo Park, CA, USA",
    },
    {
        "company_name": "Amazon",
        "profile_slug": "amazon-com",
        "trust_score": 79,
        "risk_level": "MEDIUM",
        "avg_rating": 3.95,
        "review_count": 8741,
        "sentiment_positive_pct": 72.1,
        "sentiment_negative_pct": 27.9,
        "score_breakdown": {
            "base_rating": 39.5,
            "volume_bonus": 15.0,
            "sentiment_bonus": 11.1,
            "source_diversity_bonus": 6.0,
            "recency_bonus": 4.5,
            "consistency_bonus": 2.9,
        },
        "data_freshness": "2026-05-28T12:00:00Z",
        "country": "United States",
        "industry": "E-Commerce / Cloud",
        "founded_year": 1994,
        "employee_count": 1540000,
        "headquarters": "Seattle, WA, USA",
    },
    {
        "company_name": "Tesla",
        "profile_slug": "tesla-inc",
        "trust_score": 58,
        "risk_level": "MEDIUM",
        "avg_rating": 3.30,
        "review_count": 3412,
        "sentiment_positive_pct": 52.4,
        "sentiment_negative_pct": 47.6,
        "score_breakdown": {
            "base_rating": 33.0,
            "volume_bonus": 15.0,
            "sentiment_bonus": 2.4,
            "source_diversity_bonus": 5.0,
            "recency_bonus": 1.5,
            "consistency_bonus": 1.1,
        },
        "data_freshness": "2026-05-27T18:20:00Z",
        "country": "United States",
        "industry": "Automotive / Energy",
        "founded_year": 2003,
        "employee_count": 140000,
        "headquarters": "Austin, TX, USA",
    },
    {
        "company_name": "Deutsche Bank",
        "profile_slug": "deutsche-bank",
        "trust_score": 45,
        "risk_level": "HIGH",
        "avg_rating": 3.00,
        "review_count": 987,
        "sentiment_positive_pct": 41.2,
        "sentiment_negative_pct": 58.8,
        "score_breakdown": {
            "base_rating": 30.0,
            "volume_bonus": 12.0,
            "sentiment_bonus": 0.0,
            "source_diversity_bonus": 3.0,
            "recency_bonus": 0.0,
            "consistency_bonus": 0.0,
        },
        "data_freshness": "2026-05-25T14:10:00Z",
        "country": "Germany",
        "industry": "Banking / Financial Services",
        "founded_year": 1870,
        "employee_count": 87000,
        "headquarters": "Frankfurt, Germany",
    },
    {
        "company_name": "Siemens",
        "profile_slug": "siemens-ag",
        "trust_score": 85,
        "risk_level": "LOW",
        "avg_rating": 4.20,
        "review_count": 1832,
        "sentiment_positive_pct": 79.5,
        "sentiment_negative_pct": 20.5,
        "score_breakdown": {
            "base_rating": 42.0,
            "volume_bonus": 15.0,
            "sentiment_bonus": 14.5,
            "source_diversity_bonus": 6.0,
            "recency_bonus": 4.0,
            "consistency_bonus": 3.5,
        },
        "data_freshness": "2026-05-24T09:00:00Z",
        "country": "Germany",
        "industry": "Industrial Conglomerate",
        "founded_year": 1847,
        "employee_count": 320000,
        "headquarters": "Munich, Germany",
    },
    {
        "company_name": "Bosch",
        "profile_slug": "robert-bosch",
        "trust_score": 87,
        "risk_level": "LOW",
        "avg_rating": 4.28,
        "review_count": 1456,
        "sentiment_positive_pct": 80.9,
        "sentiment_negative_pct": 19.1,
        "score_breakdown": {
            "base_rating": 42.8,
            "volume_bonus": 15.0,
            "sentiment_bonus": 14.9,
            "source_diversity_bonus": 6.0,
            "recency_bonus": 4.5,
            "consistency_bonus": 3.8,
        },
        "data_freshness": "2026-05-23T11:30:00Z",
        "country": "Germany",
        "industry": "Engineering / Automotive Parts",
        "founded_year": 1886,
        "employee_count": 421000,
        "headquarters": "Gerlingen, Germany",
    },
    {
        "company_name": "Lidl",
        "profile_slug": "lidl-stiftung",
        "trust_score": 71,
        "risk_level": "MEDIUM",
        "avg_rating": 3.70,
        "review_count": 2103,
        "sentiment_positive_pct": 64.8,
        "sentiment_negative_pct": 35.2,
        "score_breakdown": {
            "base_rating": 37.0,
            "volume_bonus": 15.0,
            "sentiment_bonus": 7.8,
            "source_diversity_bonus": 5.0,
            "recency_bonus": 3.0,
            "consistency_bonus": 3.2,
        },
        "data_freshness": "2026-05-22T07:45:00Z",
        "country": "Germany",
        "industry": "Retail / Grocery",
        "founded_year": 1973,
        "employee_count": 370000,
        "headquarters": "Neckarsulm, Germany",
    },
    {
        "company_name": "Volkswagen",
        "profile_slug": "volkswagen-ag",
        "trust_score": 62,
        "risk_level": "MEDIUM",
        "avg_rating": 3.50,
        "review_count": 1654,
        "sentiment_positive_pct": 56.7,
        "sentiment_negative_pct": 43.3,
        "score_breakdown": {
            "base_rating": 35.0,
            "volume_bonus": 15.0,
            "sentiment_bonus": 3.7,
            "source_diversity_bonus": 5.0,
            "recency_bonus": 2.0,
            "consistency_bonus": 1.3,
        },
        "data_freshness": "2026-05-21T13:20:00Z",
        "country": "Germany",
        "industry": "Automotive",
        "founded_year": 1937,
        "employee_count": 680000,
        "headquarters": "Wolfsburg, Germany",
    },
    {
        "company_name": "Microsoft",
        "profile_slug": "microsoft-corp",
        "trust_score": 90,
        "risk_level": "LOW",
        "avg_rating": 4.45,
        "review_count": 5672,
        "sentiment_positive_pct": 83.6,
        "sentiment_negative_pct": 16.4,
        "score_breakdown": {
            "base_rating": 44.5,
            "volume_bonus": 15.0,
            "sentiment_bonus": 14.6,
            "source_diversity_bonus": 6.0,
            "recency_bonus": 5.0,
            "consistency_bonus": 4.9,
        },
        "data_freshness": "2026-05-28T06:30:00Z",
        "country": "United States",
        "industry": "Technology / Cloud",
        "founded_year": 1975,
        "employee_count": 221000,
        "headquarters": "Redmond, WA, USA",
    },
    {
        "company_name": "Netflix",
        "profile_slug": "netflix-inc",
        "trust_score": 73,
        "risk_level": "MEDIUM",
        "avg_rating": 3.80,
        "review_count": 1287,
        "sentiment_positive_pct": 67.4,
        "sentiment_negative_pct": 32.6,
        "score_breakdown": {
            "base_rating": 38.0,
            "volume_bonus": 14.0,
            "sentiment_bonus": 8.4,
            "source_diversity_bonus": 5.0,
            "recency_bonus": 4.0,
            "consistency_bonus": 3.6,
        },
        "data_freshness": "2026-05-26T15:00:00Z",
        "country": "United States",
        "industry": "Entertainment / Streaming",
        "founded_year": 1997,
        "employee_count": 13000,
        "headquarters": "Los Gatos, CA, USA",
    },
    {
        "company_name": "Uber",
        "profile_slug": "uber-technologies",
        "trust_score": 52,
        "risk_level": "HIGH",
        "avg_rating": 3.10,
        "review_count": 4567,
        "sentiment_positive_pct": 47.3,
        "sentiment_negative_pct": 52.7,
        "score_breakdown": {
            "base_rating": 31.0,
            "volume_bonus": 15.0,
            "sentiment_bonus": 0.0,
            "source_diversity_bonus": 4.0,
            "recency_bonus": 1.5,
            "consistency_bonus": 0.5,
        },
        "data_freshness": "2026-05-27T11:15:00Z",
        "country": "United States",
        "industry": "Ride-sharing / Mobility",
        "founded_year": 2009,
        "employee_count": 32000,
        "headquarters": "San Francisco, CA, USA",
    },
    {
        "company_name": "WeWork",
        "profile_slug": "wework-inc",
        "trust_score": 22,
        "risk_level": "CRITICAL",
        "avg_rating": 1.90,
        "review_count": 876,
        "sentiment_positive_pct": 18.5,
        "sentiment_negative_pct": 81.5,
        "score_breakdown": {
            "base_rating": 9.5,
            "volume_bonus": 8.0,
            "sentiment_bonus": 0.0,
            "source_diversity_bonus": 3.0,
            "recency_bonus": 0.0,
            "consistency_bonus": 1.5,
        },
        "data_freshness": "2026-05-15T10:00:00Z",
        "country": "United States",
        "industry": "Co-working / Real Estate",
        "founded_year": 2010,
        "employee_count": 0,
        "headquarters": "New York, NY, USA",
    },
    {
        "company_name": "Theranos",
        "profile_slug": "theranos-inc",
        "trust_score": 8,
        "risk_level": "CRITICAL",
        "avg_rating": 1.30,
        "review_count": 234,
        "sentiment_positive_pct": 5.1,
        "sentiment_negative_pct": 94.9,
        "score_breakdown": {
            "base_rating": 3.0,
            "volume_bonus": 2.0,
            "sentiment_bonus": 0.0,
            "source_diversity_bonus": 2.0,
            "recency_bonus": 0.0,
            "consistency_bonus": 1.0,
        },
        "data_freshness": "2026-05-10T08:00:00Z",
        "country": "United States",
        "industry": "Health Technology",
        "founded_year": 2003,
        "employee_count": 0,
        "headquarters": "Palo Alto, CA, USA (dissolved)",
    },
    {
        "company_name": "Revolut",
        "profile_slug": "revolut-ltd",
        "trust_score": 68,
        "risk_level": "MEDIUM",
        "avg_rating": 3.65,
        "review_count": 1876,
        "sentiment_positive_pct": 62.3,
        "sentiment_negative_pct": 37.7,
        "score_breakdown": {
            "base_rating": 36.5,
            "volume_bonus": 15.0,
            "sentiment_bonus": 6.3,
            "source_diversity_bonus": 4.0,
            "recency_bonus": 3.5,
            "consistency_bonus": 2.7,
        },
        "data_freshness": "2026-05-27T09:45:00Z",
        "country": "United Kingdom",
        "industry": "Fintech / Neobank",
        "founded_year": 2015,
        "employee_count": 8000,
        "headquarters": "London, UK",
    },
    {
        "company_name": "N26",
        "profile_slug": "n26-gmbh",
        "trust_score": 61,
        "risk_level": "MEDIUM",
        "avg_rating": 3.45,
        "review_count": 534,
        "sentiment_positive_pct": 55.8,
        "sentiment_negative_pct": 44.2,
        "score_breakdown": {
            "base_rating": 34.5,
            "volume_bonus": 10.0,
            "sentiment_bonus": 3.8,
            "source_diversity_bonus": 4.0,
            "recency_bonus": 5.0,
            "consistency_bonus": 3.7,
        },
        "data_freshness": "2026-05-26T08:30:00Z",
        "country": "Germany",
        "industry": "Fintech / Neobank",
        "founded_year": 2013,
        "employee_count": 1500,
        "headquarters": "Berlin, Germany",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# DATA — Reviews (50+)
# ═══════════════════════════════════════════════════════════════════════════

REVIEWS: list[dict] = [
    # --- SAP (3) ---
    {"company_slug": "sap-se", "source": "kununu", "rating": 4.0, "title": "Good work-life balance, slow decision making", "text": "Great benefits and flexible hours. The bureaucracy can be frustrating though — decisions take forever.", "sentiment": "POSITIVE", "date": "2026-04-15T10:00:00Z", "verified": True},
    {"company_slug": "sap-se", "source": "glassdoor", "rating": 3.5, "title": "Stable but bureaucratic", "text": "Job security is excellent and pay is competitive. Innovation moves at a glacial pace compared to startups.", "sentiment": "NEUTRAL", "date": "2026-03-28T14:20:00Z", "verified": True},
    {"company_slug": "sap-se", "source": "google", "rating": 4.2, "title": "Great benefits and international culture", "text": "Truly global company with opportunities to work across continents. The S/4HANA transition keeps things interesting.", "sentiment": "POSITIVE", "date": "2026-05-01T09:30:00Z", "verified": False},
    # --- BMW (3) ---
    {"company_slug": "bmw-group", "source": "kununu", "rating": 4.5, "title": "Premium employer — lives up to the brand", "text": "Excellent engineering culture. The Munich campus is world-class and the company car program is unbeatable.", "sentiment": "POSITIVE", "date": "2026-04-20T08:15:00Z", "verified": True},
    {"company_slug": "bmw-group", "source": "glassdoor", "rating": 4.0, "title": "Strong brand, traditional hierarchy", "text": "Great pay and benefits. The transition to EVs creates exciting opportunities but also internal tension.", "sentiment": "POSITIVE", "date": "2026-03-15T11:30:00Z", "verified": True},
    {"company_slug": "bmw-group", "source": "indeed", "rating": 3.8, "title": "Good but competitive internally", "text": "High-performing culture that can feel intense. Not the best place for people who want a relaxed pace.", "sentiment": "NEUTRAL", "date": "2026-05-10T16:00:00Z", "verified": True},
    # --- Wirecard (3) ---
    {"company_slug": "wirecard-ag", "source": "kununu", "rating": 1.5, "title": "Fraud from the top — toxic culture", "text": "Management lied about everything. Employees were kept in the dark while billions were fabricated.", "sentiment": "NEGATIVE", "date": "2026-01-10T10:00:00Z", "verified": True},
    {"company_slug": "wirecard-ag", "source": "glassdoor", "rating": 2.0, "title": "Disaster — avoid at all costs", "text": "Company collapsed after massive accounting fraud was exposed. Careers destroyed overnight.", "sentiment": "NEGATIVE", "date": "2025-12-05T14:00:00Z", "verified": True},
    {"company_slug": "wirecard-ag", "source": "google", "rating": 1.0, "title": "Criminal enterprise disguised as fintech", "text": "€1.9 billion hole in the balance sheet. CEO arrested. Complete institutional failure.", "sentiment": "NEGATIVE", "date": "2026-02-18T09:00:00Z", "verified": False},
    # --- Google (4) ---
    {"company_slug": "google-llc", "source": "glassdoor", "rating": 4.6, "title": "Best engineering culture in the world", "text": "Access to incredible infrastructure and smart colleagues. Internal mobility is unmatched.", "sentiment": "POSITIVE", "date": "2026-05-15T10:30:00Z", "verified": True},
    {"company_slug": "google-llc", "source": "kununu", "rating": 4.3, "title": "Top-tier compensation and perks", "text": "The perks are real — free food, gym, generous RSUs. Work can be political at senior levels.", "sentiment": "POSITIVE", "date": "2026-04-28T12:00:00Z", "verified": True},
    {"company_slug": "google-llc", "source": "indeed", "rating": 4.5, "title": "Dream workplace for engineers", "text": "20% time projects still happen. The interview process is tough but fair.", "sentiment": "POSITIVE", "date": "2026-05-20T09:00:00Z", "verified": True},
    {"company_slug": "google-llc", "source": "google", "rating": 4.8, "title": "Innovation at scale", "text": "Working on products used by billions. The AI/ML resources available internally are mind-blowing.", "sentiment": "POSITIVE", "date": "2026-05-25T15:00:00Z", "verified": False},
    # --- Apple (3) ---
    {"company_slug": "apple-inc", "source": "glassdoor", "rating": 4.4, "title": "Secretive but rewarding", "text": "The culture of secrecy can be isolating, but the pride in shipping great products is real.", "sentiment": "POSITIVE", "date": "2026-05-12T08:30:00Z", "verified": True},
    {"company_slug": "apple-inc", "source": "indeed", "rating": 4.2, "title": "Hardware excellence, intense pace", "text": "Building the best hardware in the world comes with pressure. Long hours around launches.", "sentiment": "POSITIVE", "date": "2026-04-18T13:00:00Z", "verified": True},
    {"company_slug": "apple-inc", "source": "kununu", "rating": 4.5, "title": "Premium brand, premium workplace", "text": "Amazing retail employee benefits. Apple University is genuinely educational.", "sentiment": "POSITIVE", "date": "2026-05-05T10:45:00Z", "verified": True},
    # --- Meta (3) ---
    {"company_slug": "meta-platforms", "source": "glassdoor", "rating": 3.5, "title": "Great pay, questionable mission", "text": "Compensation is top-tier but morale has suffered after multiple rounds of layoffs. Metaverse pivot is divisive.", "sentiment": "NEUTRAL", "date": "2026-05-08T11:00:00Z", "verified": True},
    {"company_slug": "meta-platforms", "source": "kununu", "rating": 3.2, "title": "Move fast and break things — including teams", "text": "Constant reorgs make it hard to build anything lasting. The hackathon culture is still fun though.", "sentiment": "NEGATIVE", "date": "2026-04-22T14:30:00Z", "verified": True},
    {"company_slug": "meta-platforms", "source": "indeed", "rating": 4.0, "title": "Best bootcamp for new grads", "text": "If you can handle the pace, the learning curve is incredible. Stock has recovered nicely.", "sentiment": "POSITIVE", "date": "2026-05-18T09:15:00Z", "verified": True},
    # --- Amazon (4) ---
    {"company_slug": "amazon-com", "source": "glassdoor", "rating": 3.8, "title": "Leadership principles are real", "text": "The bar raiser process ensures quality hires. Work-life balance depends entirely on your team.", "sentiment": "POSITIVE", "date": "2026-05-20T08:00:00Z", "verified": True},
    {"company_slug": "amazon-com", "source": "indeed", "rating": 3.5, "title": "Warehouse work is tough but pays well", "text": "Physical demands are high. $21/hr starting wage and good health benefits from day one.", "sentiment": "NEUTRAL", "date": "2026-04-10T06:30:00Z", "verified": True},
    {"company_slug": "amazon-com", "source": "kununu", "rating": 4.2, "title": "AWS is a different world", "text": "AWS engineers live in a different bubble — great comp, interesting problems, but on-call is brutal.", "sentiment": "POSITIVE", "date": "2026-05-14T12:00:00Z", "verified": True},
    {"company_slug": "amazon-com", "source": "google", "rating": 3.0, "title": "PIP culture is exhausting", "text": "Performance management feels punitive. The stack ranking creates unnecessary competition.", "sentiment": "NEGATIVE", "date": "2026-03-30T17:00:00Z", "verified": False},
    # --- Tesla (3) ---
    {"company_slug": "tesla-inc", "source": "glassdoor", "rating": 3.0, "title": "Mission-driven but chaotic", "text": "You'll work on cutting-edge tech but management is unpredictable. Elon's tweets affect morale.", "sentiment": "NEUTRAL", "date": "2026-05-10T10:00:00Z", "verified": True},
    {"company_slug": "tesla-inc", "source": "indeed", "rating": 2.8, "title": "High burnout, high impact", "text": "Factory work is demanding. The mission of sustainable energy keeps people going despite challenges.", "sentiment": "NEGATIVE", "date": "2026-04-25T07:00:00Z", "verified": True},
    {"company_slug": "tesla-inc", "source": "kununu", "rating": 3.5, "title": "Gigafactory Berlin — mixed feelings", "text": "The Berlin plant has growing pains. German work culture clashing with Silicon Valley expectations.", "sentiment": "NEUTRAL", "date": "2026-05-22T14:30:00Z", "verified": True},
    # --- Deutsche Bank (3) ---
    {"company_slug": "deutsche-bank", "source": "glassdoor", "rating": 3.0, "title": "Legacy institution struggling to modernize", "text": "Good base salary but constant restructuring kills morale. Compliance overhead is enormous.", "sentiment": "NEUTRAL", "date": "2026-04-30T11:00:00Z", "verified": True},
    {"company_slug": "deutsche-bank", "source": "kununu", "rating": 2.5, "title": "Scandal after scandal erodes trust", "text": "Multiple fines for money laundering and rate manipulation. Hard to be proud of where you work.", "sentiment": "NEGATIVE", "date": "2026-03-20T09:00:00Z", "verified": True},
    {"company_slug": "deutsche-bank", "source": "indeed", "rating": 3.2, "title": "IT transformation is real", "text": "The tech division is hiring aggressively and modernizing. But cultural change is slow.", "sentiment": "NEUTRAL", "date": "2026-05-05T13:45:00Z", "verified": True},
    # --- Siemens (3) ---
    {"company_slug": "siemens-ag", "source": "kununu", "rating": 4.3, "title": "Engineering excellence with German precision", "text": "World-class R&D facilities. The spin-off strategy (Healthineers, Energy) shows strategic clarity.", "sentiment": "POSITIVE", "date": "2026-05-15T08:00:00Z", "verified": True},
    {"company_slug": "siemens-ag", "source": "glassdoor", "rating": 4.1, "title": "Stable, innovative, well-managed", "text": "CEO Roland Busch has brought focus. Digital Industries division is genuinely exciting.", "sentiment": "POSITIVE", "date": "2026-04-08T12:30:00Z", "verified": True},
    {"company_slug": "siemens-ag", "source": "indeed", "rating": 4.0, "title": "Great for long-term careers", "text": "Excellent internal mobility and global rotation programs. Pension scheme is very generous.", "sentiment": "POSITIVE", "date": "2026-05-20T10:15:00Z", "verified": True},
    # --- Microsoft (3) ---
    {"company_slug": "microsoft-corp", "source": "glassdoor", "rating": 4.5, "title": "Satya transformed the culture", "text": "Growth mindset is more than a buzzword here. Azure and AI investments are paying off big time.", "sentiment": "POSITIVE", "date": "2026-05-22T09:00:00Z", "verified": True},
    {"company_slug": "microsoft-corp", "source": "kununu", "rating": 4.3, "title": "Best large tech employer in 2026", "text": "Inclusive culture, competitive comp, and the Copilot momentum is electric.", "sentiment": "POSITIVE", "date": "2026-05-10T14:00:00Z", "verified": True},
    {"company_slug": "microsoft-corp", "source": "indeed", "rating": 4.4, "title": "Remote-friendly and flexible", "text": "Hybrid work policy is genuine. Teams/Outlook ecosystem works seamlessly for remote collaboration.", "sentiment": "POSITIVE", "date": "2026-04-28T11:30:00Z", "verified": True},
    # --- Theranos (3) ---
    {"company_slug": "theranos-inc", "source": "glassdoor", "rating": 1.2, "title": "The biggest fraud in biotech history", "text": "Elizabeth Holmes created a culture of fear and secrecy. The technology never worked.", "sentiment": "NEGATIVE", "date": "2025-06-15T10:00:00Z", "verified": True},
    {"company_slug": "theranos-inc", "source": "indeed", "rating": 1.0, "title": "Criminal enterprise — do not work here", "text": "Fake demos for investors, intimidation of whistleblowers. A cautionary tale for all of Silicon Valley.", "sentiment": "NEGATIVE", "date": "2025-08-20T08:00:00Z", "verified": True},
    {"company_slug": "theranos-inc", "source": "google", "rating": 1.5, "title": "Toxic doesn't begin to describe it", "text": "Patients received false blood test results. Lives were put at risk for investor presentations.", "sentiment": "NEGATIVE", "date": "2025-10-01T12:00:00Z", "verified": False},
    # --- WeWork (3) ---
    {"company_slug": "wework-inc", "source": "glassdoor", "rating": 2.0, "title": "Vision without substance", "text": "Adam Neumann's cult of personality masked fundamental business problems. IPO collapse was inevitable.", "sentiment": "NEGATIVE", "date": "2025-11-10T09:00:00Z", "verified": True},
    {"company_slug": "wework-inc", "source": "kununu", "rating": 1.8, "title": "Bankruptcy was the final chapter", "text": "$47B valuation to bankruptcy. The community managers were great but couldn't save a broken model.", "sentiment": "NEGATIVE", "date": "2026-01-20T10:30:00Z", "verified": True},
    {"company_slug": "wework-inc", "source": "indeed", "rating": 2.2, "title": "Fun culture, no business model", "text": "Free beer and yoga don't make up for losing $3B per year. Investors paid the price.", "sentiment": "NEGATIVE", "date": "2026-02-05T14:00:00Z", "verified": True},
    # --- Revolut (3) ---
    {"company_slug": "revolut-ltd", "source": "glassdoor", "rating": 3.5, "title": "Fast-paced fintech with growing pains", "text": "Incredible product velocity but the pressure is relentless. Burnout is a real concern.", "sentiment": "NEUTRAL", "date": "2026-05-18T10:00:00Z", "verified": True},
    {"company_slug": "revolut-ltd", "source": "kununu", "rating": 3.8, "title": "Banking license was a turning point", "text": "Getting the UK banking license added legitimacy. The product is genuinely best-in-class for travel.", "sentiment": "POSITIVE", "date": "2026-04-30T08:30:00Z", "verified": True},
    {"company_slug": "revolut-ltd", "source": "indeed", "rating": 3.2, "title": "Aggressive targets, high turnover", "text": "KPI culture can feel dehumanizing. Great learning opportunity for the first 18 months.", "sentiment": "NEUTRAL", "date": "2026-05-12T13:00:00Z", "verified": True},
    # --- N26 (3) ---
    {"company_slug": "n26-gmbh", "source": "kununu", "rating": 3.4, "title": "Berlin startup with banking ambitions", "text": "Cool office, young team. BaFin restrictions have slowed growth. Product is slick but limited.", "sentiment": "NEUTRAL", "date": "2026-05-08T09:00:00Z", "verified": True},
    {"company_slug": "n26-gmbh", "source": "glassdoor", "rating": 3.2, "title": "Regulatory headwinds hurt morale", "text": "Customer growth cap from BaFin was demoralizing. The tech stack is modern and the team is talented.", "sentiment": "NEUTRAL", "date": "2026-04-15T11:00:00Z", "verified": True},
    {"company_slug": "n26-gmbh", "source": "indeed", "rating": 3.8, "title": "Great product, uncertain future", "text": "The app UX is best-in-class. Profitability remains a question mark in a crowded neobank market.", "sentiment": "POSITIVE", "date": "2026-05-20T15:30:00Z", "verified": True},
    # --- Netflix (3) ---
    {"company_slug": "netflix-inc", "source": "glassdoor", "rating": 4.0, "title": "Freedom and responsibility — truly", "text": "The culture doc is real. You get enormous autonomy but are expected to perform at an elite level.", "sentiment": "POSITIVE", "date": "2026-05-16T10:00:00Z", "verified": True},
    {"company_slug": "netflix-inc", "source": "indeed", "rating": 3.5, "title": "Keeper test keeps you on edge", "text": "Generous severance if you're let go, but the constant evaluation is stressful.", "sentiment": "NEUTRAL", "date": "2026-04-20T09:30:00Z", "verified": True},
    {"company_slug": "netflix-inc", "source": "kununu", "rating": 3.8, "title": "Top-of-market comp, high expectations", "text": "No formal performance reviews but peers evaluate you constantly. Great for self-starters.", "sentiment": "POSITIVE", "date": "2026-05-02T12:00:00Z", "verified": True},
    # --- Uber (3) ---
    {"company_slug": "uber-technologies", "source": "glassdoor", "rating": 3.2, "title": "Post-Kalanick culture is improving", "text": "Dara brought stability but growth is slowing. Engineering is solid, product is mature.", "sentiment": "NEUTRAL", "date": "2026-05-14T10:00:00Z", "verified": True},
    {"company_slug": "uber-technologies", "source": "indeed", "rating": 2.8, "title": "Driver experience could be better", "text": "Earnings per hour have declined. Support for drivers feels like an afterthought.", "sentiment": "NEGATIVE", "date": "2026-04-28T07:00:00Z", "verified": True},
    {"company_slug": "uber-technologies", "source": "kununu", "rating": 3.0, "title": "Safety concerns still linger", "text": "Background check improvements are welcome but incidents still make headlines.", "sentiment": "NEGATIVE", "date": "2026-05-06T14:00:00Z", "verified": True},
    # --- Bosch (3) ---
    {"company_slug": "robert-bosch", "source": "kununu", "rating": 4.4, "title": "Foundation-owned = long-term thinking", "text": "No quarterly earnings pressure means genuine R&D investment. IoT division is innovative.", "sentiment": "POSITIVE", "date": "2026-05-18T08:00:00Z", "verified": True},
    {"company_slug": "robert-bosch", "source": "glassdoor", "rating": 4.2, "title": "Quiet excellence in engineering", "text": "Not as flashy as tech giants but builds products that last decades. Automotive pivot to EVs is promising.", "sentiment": "POSITIVE", "date": "2026-04-12T11:00:00Z", "verified": True},
    {"company_slug": "robert-bosch", "source": "indeed", "rating": 4.0, "title": "Great apprenticeship programs", "text": "German dual-education model at its best. Generous benefits and genuine career development.", "sentiment": "POSITIVE", "date": "2026-05-08T10:30:00Z", "verified": True},
    # --- Lidl (2) ---
    {"company_slug": "lidl-stiftung", "source": "kununu", "rating": 3.5, "title": "Discount retail with above-average pay", "text": "Surprisingly good salary for retail. Work is physically demanding and shifts are long.", "sentiment": "NEUTRAL", "date": "2026-04-25T07:00:00Z", "verified": True},
    {"company_slug": "lidl-stiftung", "source": "indeed", "rating": 3.8, "title": "Growing international presence", "text": "Expansion into the US market shows ambition. Store managers have real autonomy.", "sentiment": "POSITIVE", "date": "2026-05-15T09:00:00Z", "verified": True},
    # --- Volkswagen (2) ---
    {"company_slug": "volkswagen-ag", "source": "kununu", "rating": 3.5, "title": "Dieselgate shadow still lingers", "text": "The emissions scandal damaged trust internally too. EV strategy under ID. brand shows promise.", "sentiment": "NEUTRAL", "date": "2026-05-10T10:00:00Z", "verified": True},
    {"company_slug": "volkswagen-ag", "source": "glassdoor", "rating": 3.3, "title": "Legacy automaker in transition", "text": "Strong IG Metall union presence ensures good conditions. Software subsidiary CARIAD has struggled.", "sentiment": "NEUTRAL", "date": "2026-04-20T13:00:00Z", "verified": True},
]


# ═══════════════════════════════════════════════════════════════════════════
# DATA — Crypto Projects
# ═══════════════════════════════════════════════════════════════════════════

CRYPTO_PROJECTS: list[dict] = [
    {
        "slug": "bitcoin",
        "name": "Bitcoin",
        "symbol": "BTC",
        "price_usd": 108432.15,
        "market_cap": 2_147_000_000_000,
        "trust_score": 92,
        "risk_level": "LOW",
        "score_breakdown": {"treasury": 19, "dev_activity": 17, "security": 20, "financials": 14, "tokenomics": 13, "community": 9},
        "project_stage": "live-token",
        "has_token": True,
        "github_org": "bitcoin",
        "commits_last_30d": 87,
        "active_devs": 34,
        "tvl": None,
        "total_raised": None,
        "lead_investors": [],
        "certik_score": None,
        "tweetscout_score": 95,
    },
    {
        "slug": "ethereum",
        "name": "Ethereum",
        "symbol": "ETH",
        "price_usd": 2647.22,
        "market_cap": 318_000_000_000,
        "trust_score": 94,
        "risk_level": "LOW",
        "score_breakdown": {"treasury": 20, "dev_activity": 19, "security": 20, "financials": 14, "tokenomics": 12, "community": 9},
        "project_stage": "live-token",
        "has_token": True,
        "github_org": "ethereum",
        "commits_last_30d": 214,
        "active_devs": 89,
        "tvl": 58_700_000_000,
        "total_raised": None,
        "lead_investors": [],
        "certik_score": None,
        "tweetscout_score": 98,
    },
    {
        "slug": "uniswap",
        "name": "Uniswap",
        "symbol": "UNI",
        "price_usd": 11.84,
        "market_cap": 7_100_000_000,
        "trust_score": 78,
        "risk_level": "MEDIUM",
        "score_breakdown": {"treasury": 16, "dev_activity": 18, "security": 16, "financials": 12, "tokenomics": 8, "community": 8},
        "project_stage": "live-token",
        "has_token": True,
        "github_org": "Uniswap",
        "commits_last_30d": 156,
        "active_devs": 42,
        "tvl": 5_200_000_000,
        "total_raised": 176_000_000,
        "lead_investors": ["a16z", "Paradigm"],
        "certik_score": 89,
        "tweetscout_score": 82,
    },
    {
        "slug": "solana",
        "name": "Solana",
        "symbol": "SOL",
        "price_usd": 178.50,
        "market_cap": 82_000_000_000,
        "trust_score": 81,
        "risk_level": "LOW",
        "score_breakdown": {"treasury": 17, "dev_activity": 18, "security": 15, "financials": 13, "tokenomics": 10, "community": 8},
        "project_stage": "live-token",
        "has_token": True,
        "github_org": "solana-labs",
        "commits_last_30d": 198,
        "active_devs": 67,
        "tvl": 8_900_000_000,
        "total_raised": 335_000_000,
        "lead_investors": ["a16z", "Multicoin Capital", "Alameda Research"],
        "certik_score": 85,
        "tweetscout_score": 91,
    },
    {
        "slug": "cardano",
        "name": "Cardano",
        "symbol": "ADA",
        "price_usd": 0.72,
        "market_cap": 25_400_000_000,
        "trust_score": 72,
        "risk_level": "MEDIUM",
        "score_breakdown": {"treasury": 14, "dev_activity": 16, "security": 16, "financials": 10, "tokenomics": 9, "community": 7},
        "project_stage": "live-token",
        "has_token": True,
        "github_org": "input-output-hk",
        "commits_last_30d": 112,
        "active_devs": 51,
        "tvl": 420_000_000,
        "total_raised": 62_000_000,
        "lead_investors": ["IOHK", "Emurgo"],
        "certik_score": 82,
        "tweetscout_score": 76,
    },
    {
        "slug": "polkadot",
        "name": "Polkadot",
        "symbol": "DOT",
        "price_usd": 5.18,
        "market_cap": 7_200_000_000,
        "trust_score": 75,
        "risk_level": "MEDIUM",
        "score_breakdown": {"treasury": 15, "dev_activity": 17, "security": 15, "financials": 11, "tokenomics": 9, "community": 8},
        "project_stage": "live-token",
        "has_token": True,
        "github_org": "paritytech",
        "commits_last_30d": 178,
        "active_devs": 58,
        "tvl": 1_200_000_000,
        "total_raised": 293_000_000,
        "lead_investors": ["Web3 Foundation"],
        "certik_score": 86,
        "tweetscout_score": 74,
    },
    {
        "slug": "chainlink",
        "name": "Chainlink",
        "symbol": "LINK",
        "price_usd": 18.45,
        "market_cap": 11_200_000_000,
        "trust_score": 83,
        "risk_level": "LOW",
        "score_breakdown": {"treasury": 17, "dev_activity": 17, "security": 18, "financials": 13, "tokenomics": 10, "community": 8},
        "project_stage": "live-token",
        "has_token": True,
        "github_org": "smartcontractkit",
        "commits_last_30d": 134,
        "active_devs": 45,
        "tvl": None,
        "total_raised": 32_000_000,
        "lead_investors": ["Framework Ventures", "Ari Paul"],
        "certik_score": 91,
        "tweetscout_score": 85,
    },
    {
        "slug": "aave",
        "name": "Aave",
        "symbol": "AAVE",
        "price_usd": 285.30,
        "market_cap": 4_200_000_000,
        "trust_score": 79,
        "risk_level": "MEDIUM",
        "score_breakdown": {"treasury": 16, "dev_activity": 16, "security": 17, "financials": 12, "tokenomics": 10, "community": 8},
        "project_stage": "live-token",
        "has_token": True,
        "github_org": "aave",
        "commits_last_30d": 89,
        "active_devs": 28,
        "tvl": 12_800_000_000,
        "total_raised": 49_000_000,
        "lead_investors": ["Framework Ventures", "Three Arrows Capital"],
        "certik_score": 90,
        "tweetscout_score": 79,
    },
    {
        "slug": "lido",
        "name": "Lido",
        "symbol": "LDO",
        "price_usd": 2.15,
        "market_cap": 1_900_000_000,
        "trust_score": 76,
        "risk_level": "MEDIUM",
        "score_breakdown": {"treasury": 15, "dev_activity": 16, "security": 16, "financials": 12, "tokenomics": 9, "community": 8},
        "project_stage": "live-token",
        "has_token": True,
        "github_org": "lidofinance",
        "commits_last_30d": 76,
        "active_devs": 22,
        "tvl": 14_500_000_000,
        "total_raised": 94_000_000,
        "lead_investors": ["a16z", "Paradigm", "Dragonfly"],
        "certik_score": 87,
        "tweetscout_score": 77,
    },
    {
        "slug": "arbitrum",
        "name": "Arbitrum",
        "symbol": "ARB",
        "price_usd": 0.95,
        "market_cap": 3_800_000_000,
        "trust_score": 70,
        "risk_level": "MEDIUM",
        "score_breakdown": {"treasury": 14, "dev_activity": 16, "security": 14, "financials": 11, "tokenomics": 8, "community": 7},
        "project_stage": "live-token",
        "has_token": True,
        "github_org": "OffchainLabs",
        "commits_last_30d": 145,
        "active_devs": 38,
        "tvl": 3_200_000_000,
        "total_raised": 123_500_000,
        "lead_investors": ["Lightspeed Venture Partners", "Polychain Capital"],
        "certik_score": 84,
        "tweetscout_score": 72,
    },
    {
        "slug": "optimism",
        "name": "Optimism",
        "symbol": "OP",
        "price_usd": 1.78,
        "market_cap": 2_100_000_000,
        "trust_score": 69,
        "risk_level": "MEDIUM",
        "score_breakdown": {"treasury": 14, "dev_activity": 15, "security": 14, "financials": 11, "tokenomics": 8, "community": 7},
        "project_stage": "live-token",
        "has_token": True,
        "github_org": "ethereum-optimism",
        "commits_last_30d": 167,
        "active_devs": 35,
        "tvl": 1_800_000_000,
        "total_raised": 178_500_000,
        "lead_investors": ["a16z", "Paradigm"],
        "certik_score": 83,
        "tweetscout_score": 70,
    },
    {
        "slug": "dydx",
        "name": "dYdX",
        "symbol": "DYDX",
        "price_usd": 1.42,
        "market_cap": 870_000_000,
        "trust_score": 67,
        "risk_level": "MEDIUM",
        "score_breakdown": {"treasury": 13, "dev_activity": 15, "security": 14, "financials": 10, "tokenomics": 8, "community": 7},
        "project_stage": "live-token",
        "has_token": True,
        "github_org": "dydxprotocol",
        "commits_last_30d": 98,
        "active_devs": 24,
        "tvl": 340_000_000,
        "total_raised": 87_000_000,
        "lead_investors": ["a16z", "Polychain Capital", "Paradigm"],
        "certik_score": 81,
        "tweetscout_score": 65,
    },
    # --- CRITICAL / Collapsed ---
    {
        "slug": "ftx-token",
        "name": "FTX Token",
        "symbol": "FTT",
        "price_usd": 0.82,
        "market_cap": 270_000_000,
        "trust_score": 5,
        "risk_level": "CRITICAL",
        "score_breakdown": {"treasury": 0, "dev_activity": 0, "security": 0, "financials": 0, "tokenomics": 2, "community": 3},
        "project_stage": "collapsed",
        "has_token": True,
        "github_org": None,
        "commits_last_30d": 0,
        "active_devs": 0,
        "tvl": 0,
        "total_raised": 1_800_000_000,
        "lead_investors": ["Sequoia Capital", "SoftBank", "Tiger Global"],
        "certik_score": None,
        "tweetscout_score": 8,
    },
    {
        "slug": "terra-luna",
        "name": "Terra / Luna",
        "symbol": "LUNA",
        "price_usd": 0.00012,
        "market_cap": 830_000,
        "trust_score": 3,
        "risk_level": "CRITICAL",
        "score_breakdown": {"treasury": 0, "dev_activity": 1, "security": 0, "financials": 0, "tokenomics": 0, "community": 2},
        "project_stage": "collapsed",
        "has_token": True,
        "github_org": "terra-money",
        "commits_last_30d": 0,
        "active_devs": 0,
        "tvl": 0,
        "total_raised": 150_000_000,
        "lead_investors": ["Galaxy Digital", "Pantera Capital", "Coinbase Ventures"],
        "certik_score": None,
        "tweetscout_score": 5,
    },
    {
        "slug": "safemoon",
        "name": "SafeMoon",
        "symbol": "SFM",
        "price_usd": 0.000034,
        "market_cap": 19_200_000,
        "trust_score": 12,
        "risk_level": "CRITICAL",
        "score_breakdown": {"treasury": 2, "dev_activity": 1, "security": 2, "financials": 1, "tokenomics": 3, "community": 3},
        "project_stage": "collapsed",
        "has_token": True,
        "github_org": "safemoon",
        "commits_last_30d": 0,
        "active_devs": 0,
        "tvl": 0,
        "total_raised": None,
        "lead_investors": [],
        "certik_score": 32,
        "tweetscout_score": 15,
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# DATA — Wallets
# ═══════════════════════════════════════════════════════════════════════════

WALLETS: list[dict] = [
    {
        "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        "eth_balance": 1247.83,
        "usd_value": 3_303_530.27,
        "label": "vitalik.eth",
        "chain": "ethereum",
        "risk_flags": [],
        "last_activity": "2026-05-28T14:22:00Z",
    },
    {
        "address": "0x28C6c06298d514Db089934071355E5743bf21d60",
        "eth_balance": 892451.20,
        "usd_value": 2_362_157_926.40,
        "label": "Binance Hot Wallet",
        "chain": "ethereum",
        "risk_flags": [],
        "last_activity": "2026-05-29T08:00:00Z",
    },
    {
        "address": "0xDFd5293D8e347dFe59E90eFd55b2956a1343963d",
        "eth_balance": 541203.75,
        "usd_value": 1_432_564_324.75,
        "label": "Coinbase Cold Storage",
        "chain": "ethereum",
        "risk_flags": [],
        "last_activity": "2026-05-27T22:15:00Z",
    },
    {
        "address": "0x71660c4005BA85c37ccec55d0C4493E66Fe775d3",
        "eth_balance": 124.50,
        "usd_value": 329_578.90,
        "label": "Coinbase Commerce",
        "chain": "ethereum",
        "risk_flags": [],
        "last_activity": "2026-05-28T19:30:00Z",
    },
    {
        "address": "0x1f9090aaE28b8a3dCeaDf281B0F12828e676c326",
        "eth_balance": 3214.67,
        "usd_value": 8_509_235.07,
        "label": "rsync-builder.eth (MEV Builder)",
        "chain": "ethereum",
        "risk_flags": ["mev_activity"],
        "last_activity": "2026-05-29T10:45:00Z",
    },
    {
        "address": "0x00000000219ab540356cBB839Cbe05303d7705Fa",
        "eth_balance": 52_617_843.00,
        "usd_value": 139_277_220_249.00,
        "label": "ETH2 Deposit Contract",
        "chain": "ethereum",
        "risk_flags": [],
        "last_activity": "2026-05-29T11:00:00Z",
    },
    {
        "address": "0x8576aCC5C05D6Ce88f4e49bf65BdF0C62F91353C",
        "eth_balance": 45.20,
        "usd_value": 119_656.84,
        "label": "Unknown — Tornado Cash Interaction",
        "chain": "ethereum",
        "risk_flags": ["tornado_cash_interaction", "sanctions_risk", "high_risk_mixer"],
        "last_activity": "2026-05-20T03:15:00Z",
    },
    {
        "address": "0x3CBdeD43EFdAf0FC77b9C55F6fC9988fCC9b757d",
        "eth_balance": 0.001,
        "usd_value": 2.65,
        "label": "Suspected Phishing — Fake Airdrop",
        "chain": "ethereum",
        "risk_flags": ["phishing", "fake_airdrop", "dust_attack"],
        "last_activity": "2026-05-22T17:00:00Z",
    },
    {
        "address": "0xA7EFAe728D2936e78BDA97dc267687568dD593f3",
        "eth_balance": 2187.45,
        "usd_value": 5_790_122.49,
        "label": "Unknown — FTX Recovery Wallet",
        "chain": "ethereum",
        "risk_flags": ["ftx_associated", "bankruptcy_estate"],
        "last_activity": "2026-05-15T06:30:00Z",
    },
    {
        "address": "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8",
        "eth_balance": 1_996_008.00,
        "usd_value": 5_283_433_176.00,
        "label": "Binance Cold Wallet 7",
        "chain": "ethereum",
        "risk_flags": [],
        "last_activity": "2026-05-26T04:00:00Z",
    },
    {
        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD1e",
        "eth_balance": 0.23,
        "usd_value": 608.86,
        "label": "Suspected Rug Pull — DeFi Exploit",
        "chain": "ethereum",
        "risk_flags": ["rug_pull", "flash_loan_exploit", "high_risk"],
        "last_activity": "2026-05-18T01:45:00Z",
    },
    {
        "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        "eth_balance": None,
        "usd_value": 52_430_000.00,
        "label": "Satoshi-era Wallet (dormant)",
        "chain": "bitcoin",
        "risk_flags": ["dormant_whale"],
        "last_activity": "2012-04-15T00:00:00Z",
    },
]



# ═══════════════════════════════════════════════════════════════════════════
# DATA ENRICHMENT — Salary, Hiring, Liquidity, Whale, DeFi fields
# ═══════════════════════════════════════════════════════════════════════════

# Per-company salary & hiring data (keyed by profile_slug)
_COMPANY_SALARY_DATA: dict[str, dict] = {
    "sap-se": {
        "salary_ranges": {
            "junior": {"min": 52000, "max": 68000, "currency": "EUR"},
            "mid": {"min": 72000, "max": 95000, "currency": "EUR"},
            "senior": {"min": 100000, "max": 135000, "currency": "EUR"},
        },
        "median_salary": 82000,
        "salary_vs_industry_avg_pct": 5.2,
        "benefits_summary": {"health_insurance": True, "remote_work": True, "stock_options": True, "pension_plan": True, "bonus_structure": "annual", "vacation_days": 30},
    },
    "bmw-group": {
        "salary_ranges": {
            "junior": {"min": 48000, "max": 62000, "currency": "EUR"},
            "mid": {"min": 68000, "max": 90000, "currency": "EUR"},
            "senior": {"min": 95000, "max": 130000, "currency": "EUR"},
        },
        "median_salary": 78000,
        "salary_vs_industry_avg_pct": 12.3,
        "benefits_summary": {"health_insurance": True, "remote_work": True, "stock_options": False, "pension_plan": True, "bonus_structure": "annual", "vacation_days": 30, "company_car": True},
    },
    "wirecard-ag": {
        "salary_ranges": {
            "junior": {"min": 40000, "max": 52000, "currency": "EUR"},
            "mid": {"min": 55000, "max": 72000, "currency": "EUR"},
            "senior": {"min": 75000, "max": 100000, "currency": "EUR"},
        },
        "median_salary": 62000,
        "salary_vs_industry_avg_pct": -18.5,
        "benefits_summary": {"health_insurance": True, "remote_work": False, "stock_options": True, "pension_plan": False, "bonus_structure": "none", "vacation_days": 25},
    },
    "google-llc": {
        "salary_ranges": {
            "junior": {"min": 95000, "max": 130000, "currency": "USD"},
            "mid": {"min": 140000, "max": 195000, "currency": "USD"},
            "senior": {"min": 210000, "max": 350000, "currency": "USD"},
        },
        "median_salary": 185000,
        "salary_vs_industry_avg_pct": 28.4,
        "benefits_summary": {"health_insurance": True, "remote_work": True, "stock_options": True, "pension_plan": True, "bonus_structure": "annual", "vacation_days": 25, "free_meals": True},
    },
    "apple-inc": {
        "salary_ranges": {
            "junior": {"min": 88000, "max": 120000, "currency": "USD"},
            "mid": {"min": 130000, "max": 185000, "currency": "USD"},
            "senior": {"min": 195000, "max": 320000, "currency": "USD"},
        },
        "median_salary": 172000,
        "salary_vs_industry_avg_pct": 22.1,
        "benefits_summary": {"health_insurance": True, "remote_work": False, "stock_options": True, "pension_plan": True, "bonus_structure": "annual", "vacation_days": 22, "product_discount": True},
    },
    "meta-platforms": {
        "salary_ranges": {
            "junior": {"min": 92000, "max": 128000, "currency": "USD"},
            "mid": {"min": 145000, "max": 200000, "currency": "USD"},
            "senior": {"min": 220000, "max": 380000, "currency": "USD"},
        },
        "median_salary": 190000,
        "salary_vs_industry_avg_pct": 30.1,
        "benefits_summary": {"health_insurance": True, "remote_work": True, "stock_options": True, "pension_plan": True, "bonus_structure": "annual", "vacation_days": 25, "free_meals": True},
    },
    "amazon-com": {
        "salary_ranges": {
            "junior": {"min": 72000, "max": 105000, "currency": "USD"},
            "mid": {"min": 115000, "max": 165000, "currency": "USD"},
            "senior": {"min": 175000, "max": 280000, "currency": "USD"},
        },
        "median_salary": 148000,
        "salary_vs_industry_avg_pct": 8.7,
        "benefits_summary": {"health_insurance": True, "remote_work": False, "stock_options": True, "pension_plan": True, "bonus_structure": "annual", "vacation_days": 20},
    },
    "tesla-inc": {
        "salary_ranges": {
            "junior": {"min": 68000, "max": 95000, "currency": "USD"},
            "mid": {"min": 100000, "max": 145000, "currency": "USD"},
            "senior": {"min": 155000, "max": 250000, "currency": "USD"},
        },
        "median_salary": 125000,
        "salary_vs_industry_avg_pct": -5.3,
        "benefits_summary": {"health_insurance": True, "remote_work": False, "stock_options": True, "pension_plan": True, "bonus_structure": "none", "vacation_days": 15},
    },
    "deutsche-bank": {
        "salary_ranges": {
            "junior": {"min": 50000, "max": 65000, "currency": "EUR"},
            "mid": {"min": 70000, "max": 95000, "currency": "EUR"},
            "senior": {"min": 105000, "max": 160000, "currency": "EUR"},
        },
        "median_salary": 85000,
        "salary_vs_industry_avg_pct": -2.1,
        "benefits_summary": {"health_insurance": True, "remote_work": True, "stock_options": False, "pension_plan": True, "bonus_structure": "annual", "vacation_days": 30},
    },
    "siemens-ag": {
        "salary_ranges": {
            "junior": {"min": 50000, "max": 65000, "currency": "EUR"},
            "mid": {"min": 70000, "max": 92000, "currency": "EUR"},
            "senior": {"min": 98000, "max": 140000, "currency": "EUR"},
        },
        "median_salary": 80000,
        "salary_vs_industry_avg_pct": 8.9,
        "benefits_summary": {"health_insurance": True, "remote_work": True, "stock_options": True, "pension_plan": True, "bonus_structure": "annual", "vacation_days": 30},
    },
    "robert-bosch": {
        "salary_ranges": {
            "junior": {"min": 48000, "max": 62000, "currency": "EUR"},
            "mid": {"min": 66000, "max": 88000, "currency": "EUR"},
            "senior": {"min": 92000, "max": 130000, "currency": "EUR"},
        },
        "median_salary": 76000,
        "salary_vs_industry_avg_pct": 6.4,
        "benefits_summary": {"health_insurance": True, "remote_work": True, "stock_options": False, "pension_plan": True, "bonus_structure": "annual", "vacation_days": 30},
    },
    "lidl-stiftung": {
        "salary_ranges": {
            "junior": {"min": 32000, "max": 42000, "currency": "EUR"},
            "mid": {"min": 45000, "max": 60000, "currency": "EUR"},
            "senior": {"min": 65000, "max": 90000, "currency": "EUR"},
        },
        "median_salary": 48000,
        "salary_vs_industry_avg_pct": 14.2,
        "benefits_summary": {"health_insurance": True, "remote_work": False, "stock_options": False, "pension_plan": True, "bonus_structure": "quarterly", "vacation_days": 28},
    },
    "volkswagen-ag": {
        "salary_ranges": {
            "junior": {"min": 46000, "max": 60000, "currency": "EUR"},
            "mid": {"min": 65000, "max": 88000, "currency": "EUR"},
            "senior": {"min": 92000, "max": 125000, "currency": "EUR"},
        },
        "median_salary": 75000,
        "salary_vs_industry_avg_pct": 3.8,
        "benefits_summary": {"health_insurance": True, "remote_work": True, "stock_options": False, "pension_plan": True, "bonus_structure": "annual", "vacation_days": 30, "company_car": True},
    },
    "microsoft-corp": {
        "salary_ranges": {
            "junior": {"min": 90000, "max": 125000, "currency": "USD"},
            "mid": {"min": 135000, "max": 190000, "currency": "USD"},
            "senior": {"min": 200000, "max": 340000, "currency": "USD"},
        },
        "median_salary": 180000,
        "salary_vs_industry_avg_pct": 25.6,
        "benefits_summary": {"health_insurance": True, "remote_work": True, "stock_options": True, "pension_plan": True, "bonus_structure": "annual", "vacation_days": 25},
    },
    "netflix-inc": {
        "salary_ranges": {
            "junior": {"min": 100000, "max": 140000, "currency": "USD"},
            "mid": {"min": 155000, "max": 220000, "currency": "USD"},
            "senior": {"min": 240000, "max": 400000, "currency": "USD"},
        },
        "median_salary": 210000,
        "salary_vs_industry_avg_pct": 38.5,
        "benefits_summary": {"health_insurance": True, "remote_work": True, "stock_options": True, "pension_plan": True, "bonus_structure": "none", "vacation_days": 0, "unlimited_pto": True},
    },
    "uber-technologies": {
        "salary_ranges": {
            "junior": {"min": 78000, "max": 108000, "currency": "USD"},
            "mid": {"min": 118000, "max": 165000, "currency": "USD"},
            "senior": {"min": 175000, "max": 280000, "currency": "USD"},
        },
        "median_salary": 142000,
        "salary_vs_industry_avg_pct": 4.2,
        "benefits_summary": {"health_insurance": True, "remote_work": True, "stock_options": True, "pension_plan": True, "bonus_structure": "annual", "vacation_days": 22},
    },
    "wework-inc": {
        "salary_ranges": {
            "junior": {"min": 45000, "max": 62000, "currency": "USD"},
            "mid": {"min": 65000, "max": 90000, "currency": "USD"},
            "senior": {"min": 95000, "max": 140000, "currency": "USD"},
        },
        "median_salary": 72000,
        "salary_vs_industry_avg_pct": -28.3,
        "benefits_summary": {"health_insurance": True, "remote_work": False, "stock_options": False, "pension_plan": False, "bonus_structure": "none", "vacation_days": 15},
    },
    "theranos-inc": {
        "salary_ranges": {
            "junior": {"min": 55000, "max": 70000, "currency": "USD"},
            "mid": {"min": 75000, "max": 100000, "currency": "USD"},
            "senior": {"min": 110000, "max": 160000, "currency": "USD"},
        },
        "median_salary": 85000,
        "salary_vs_industry_avg_pct": -22.0,
        "benefits_summary": {"health_insurance": True, "remote_work": False, "stock_options": True, "pension_plan": False, "bonus_structure": "none", "vacation_days": 15},
    },
    "revolut-ltd": {
        "salary_ranges": {
            "junior": {"min": 42000, "max": 58000, "currency": "GBP"},
            "mid": {"min": 62000, "max": 85000, "currency": "GBP"},
            "senior": {"min": 90000, "max": 140000, "currency": "GBP"},
        },
        "median_salary": 72000,
        "salary_vs_industry_avg_pct": 2.8,
        "benefits_summary": {"health_insurance": True, "remote_work": True, "stock_options": True, "pension_plan": True, "bonus_structure": "quarterly", "vacation_days": 25},
    },
    "n26-gmbh": {
        "salary_ranges": {
            "junior": {"min": 42000, "max": 55000, "currency": "EUR"},
            "mid": {"min": 58000, "max": 78000, "currency": "EUR"},
            "senior": {"min": 82000, "max": 115000, "currency": "EUR"},
        },
        "median_salary": 65000,
        "salary_vs_industry_avg_pct": -8.5,
        "benefits_summary": {"health_insurance": True, "remote_work": True, "stock_options": True, "pension_plan": True, "bonus_structure": "annual", "vacation_days": 28},
    },
}

_COMPANY_HIRING_DATA: dict[str, dict] = {
    "sap-se": {"open_positions": 487, "growth_rate_pct": 6.2, "trending_roles": ["Cloud Engineer", "AI/ML Engineer", "SAP BTP Developer", "Solution Architect"], "remote_vs_office": {"remote_pct": 35.0, "hybrid_pct": 45.0, "office_pct": 20.0}, "diversity_score": 72.5, "avg_time_to_hire_days": 38},
    "bmw-group": {"open_positions": 312, "growth_rate_pct": 3.8, "trending_roles": ["EV Powertrain Engineer", "Autonomous Driving Specialist", "Battery Chemist", "Software Engineer"], "remote_vs_office": {"remote_pct": 15.0, "hybrid_pct": 50.0, "office_pct": 35.0}, "diversity_score": 64.8, "avg_time_to_hire_days": 42},
    "wirecard-ag": {"open_positions": 0, "growth_rate_pct": -100.0, "trending_roles": [], "remote_vs_office": {"remote_pct": 0.0, "hybrid_pct": 0.0, "office_pct": 0.0}, "diversity_score": 0.0, "avg_time_to_hire_days": 0},
    "google-llc": {"open_positions": 1245, "growth_rate_pct": 8.5, "trending_roles": ["AI Research Scientist", "SRE", "Cloud Architect", "Product Manager", "Security Engineer"], "remote_vs_office": {"remote_pct": 25.0, "hybrid_pct": 55.0, "office_pct": 20.0}, "diversity_score": 78.3, "avg_time_to_hire_days": 45},
    "apple-inc": {"open_positions": 892, "growth_rate_pct": 5.1, "trending_roles": ["Apple Silicon Engineer", "ML Engineer", "iOS Developer", "Hardware Engineer"], "remote_vs_office": {"remote_pct": 10.0, "hybrid_pct": 40.0, "office_pct": 50.0}, "diversity_score": 71.2, "avg_time_to_hire_days": 48},
    "meta-platforms": {"open_positions": 634, "growth_rate_pct": -2.3, "trending_roles": ["AI Research Scientist", "VR/AR Developer", "Infrastructure Engineer", "Content Policy Specialist"], "remote_vs_office": {"remote_pct": 40.0, "hybrid_pct": 40.0, "office_pct": 20.0}, "diversity_score": 68.9, "avg_time_to_hire_days": 35},
    "amazon-com": {"open_positions": 3421, "growth_rate_pct": 4.2, "trending_roles": ["Software Dev Engineer", "AWS Solutions Architect", "Operations Manager", "Data Engineer"], "remote_vs_office": {"remote_pct": 15.0, "hybrid_pct": 35.0, "office_pct": 50.0}, "diversity_score": 62.4, "avg_time_to_hire_days": 32},
    "tesla-inc": {"open_positions": 756, "growth_rate_pct": 12.8, "trending_roles": ["Battery Engineer", "Autopilot Software Engineer", "Manufacturing Engineer", "Robotics Engineer"], "remote_vs_office": {"remote_pct": 5.0, "hybrid_pct": 15.0, "office_pct": 80.0}, "diversity_score": 48.7, "avg_time_to_hire_days": 28},
    "deutsche-bank": {"open_positions": 298, "growth_rate_pct": -1.5, "trending_roles": ["Risk Analyst", "Compliance Officer", "Quantitative Developer", "Cybersecurity Analyst"], "remote_vs_office": {"remote_pct": 20.0, "hybrid_pct": 55.0, "office_pct": 25.0}, "diversity_score": 58.1, "avg_time_to_hire_days": 52},
    "siemens-ag": {"open_positions": 567, "growth_rate_pct": 5.5, "trending_roles": ["IoT Developer", "Digital Twin Engineer", "PLM Specialist", "Industrial AI Engineer"], "remote_vs_office": {"remote_pct": 30.0, "hybrid_pct": 45.0, "office_pct": 25.0}, "diversity_score": 70.3, "avg_time_to_hire_days": 40},
    "robert-bosch": {"open_positions": 823, "growth_rate_pct": 4.1, "trending_roles": ["ADAS Engineer", "Embedded Software Developer", "EV Component Engineer", "IoT Architect"], "remote_vs_office": {"remote_pct": 20.0, "hybrid_pct": 50.0, "office_pct": 30.0}, "diversity_score": 66.7, "avg_time_to_hire_days": 36},
    "lidl-stiftung": {"open_positions": 1456, "growth_rate_pct": 7.3, "trending_roles": ["Store Manager", "Supply Chain Analyst", "E-commerce Developer", "Category Manager"], "remote_vs_office": {"remote_pct": 5.0, "hybrid_pct": 15.0, "office_pct": 80.0}, "diversity_score": 55.2, "avg_time_to_hire_days": 18},
    "volkswagen-ag": {"open_positions": 445, "growth_rate_pct": 1.2, "trending_roles": ["EV Software Engineer", "Battery Cell Developer", "Autonomous Driving Engineer", "CARIAD Developer"], "remote_vs_office": {"remote_pct": 15.0, "hybrid_pct": 45.0, "office_pct": 40.0}, "diversity_score": 60.5, "avg_time_to_hire_days": 44},
    "microsoft-corp": {"open_positions": 1678, "growth_rate_pct": 9.1, "trending_roles": ["Azure Cloud Engineer", "Copilot AI Developer", "Security Researcher", "DevOps Engineer"], "remote_vs_office": {"remote_pct": 45.0, "hybrid_pct": 40.0, "office_pct": 15.0}, "diversity_score": 82.1, "avg_time_to_hire_days": 40},
    "netflix-inc": {"open_positions": 134, "growth_rate_pct": 3.2, "trending_roles": ["Streaming Infrastructure Engineer", "Content Algorithm Engineer", "Security Engineer", "Data Scientist"], "remote_vs_office": {"remote_pct": 35.0, "hybrid_pct": 45.0, "office_pct": 20.0}, "diversity_score": 74.6, "avg_time_to_hire_days": 50},
    "uber-technologies": {"open_positions": 389, "growth_rate_pct": 2.8, "trending_roles": ["ML Platform Engineer", "Marketplace Economist", "Maps Engineer", "Safety Data Analyst"], "remote_vs_office": {"remote_pct": 30.0, "hybrid_pct": 45.0, "office_pct": 25.0}, "diversity_score": 65.3, "avg_time_to_hire_days": 34},
    "wework-inc": {"open_positions": 0, "growth_rate_pct": -100.0, "trending_roles": [], "remote_vs_office": {"remote_pct": 0.0, "hybrid_pct": 0.0, "office_pct": 0.0}, "diversity_score": 0.0, "avg_time_to_hire_days": 0},
    "theranos-inc": {"open_positions": 0, "growth_rate_pct": -100.0, "trending_roles": [], "remote_vs_office": {"remote_pct": 0.0, "hybrid_pct": 0.0, "office_pct": 0.0}, "diversity_score": 0.0, "avg_time_to_hire_days": 0},
    "revolut-ltd": {"open_positions": 267, "growth_rate_pct": 15.4, "trending_roles": ["Backend Engineer", "Compliance Analyst", "Growth Marketer", "Crypto Product Manager"], "remote_vs_office": {"remote_pct": 50.0, "hybrid_pct": 35.0, "office_pct": 15.0}, "diversity_score": 69.8, "avg_time_to_hire_days": 25},
    "n26-gmbh": {"open_positions": 78, "growth_rate_pct": -4.2, "trending_roles": ["Mobile Engineer", "Risk Analyst", "Regulatory Affairs Specialist", "Data Engineer"], "remote_vs_office": {"remote_pct": 40.0, "hybrid_pct": 40.0, "office_pct": 20.0}, "diversity_score": 72.0, "avg_time_to_hire_days": 30},
}

# Per-crypto liquidity, whale, and DeFi data (keyed by slug)
_CRYPTO_LIQUIDITY_DATA: dict[str, dict] = {
    "bitcoin": {"dex_liquidity_usd": 2_450_000_000, "trading_volume_24h_usd": 28_500_000_000, "liquidity_depth": {"plus_2_pct_usd": 850_000_000, "minus_2_pct_usd": 780_000_000}, "impermanent_loss_risk": "LOW", "major_dex_pairs": [{"pair": "BTC/USDT", "dex": "Binance", "liquidity_usd": 1_200_000_000, "volume_24h_usd": 8_500_000_000}, {"pair": "WBTC/ETH", "dex": "Uniswap V3", "liquidity_usd": 450_000_000, "volume_24h_usd": 120_000_000}], "liquidity_score": 98.2},
    "ethereum": {"dex_liquidity_usd": 3_800_000_000, "trading_volume_24h_usd": 15_200_000_000, "liquidity_depth": {"plus_2_pct_usd": 1_200_000_000, "minus_2_pct_usd": 1_050_000_000}, "impermanent_loss_risk": "LOW", "major_dex_pairs": [{"pair": "ETH/USDC", "dex": "Uniswap V3", "liquidity_usd": 980_000_000, "volume_24h_usd": 2_400_000_000}, {"pair": "ETH/USDT", "dex": "Curve", "liquidity_usd": 650_000_000, "volume_24h_usd": 1_800_000_000}], "liquidity_score": 97.5},
    "uniswap": {"dex_liquidity_usd": 285_000_000, "trading_volume_24h_usd": 245_000_000, "liquidity_depth": {"plus_2_pct_usd": 42_000_000, "minus_2_pct_usd": 38_000_000}, "impermanent_loss_risk": "MEDIUM", "major_dex_pairs": [{"pair": "UNI/ETH", "dex": "Uniswap V3", "liquidity_usd": 185_000_000, "volume_24h_usd": 95_000_000}, {"pair": "UNI/USDC", "dex": "Uniswap V3", "liquidity_usd": 72_000_000, "volume_24h_usd": 45_000_000}], "liquidity_score": 82.4},
    "solana": {"dex_liquidity_usd": 890_000_000, "trading_volume_24h_usd": 3_200_000_000, "liquidity_depth": {"plus_2_pct_usd": 280_000_000, "minus_2_pct_usd": 245_000_000}, "impermanent_loss_risk": "LOW", "major_dex_pairs": [{"pair": "SOL/USDC", "dex": "Raydium", "liquidity_usd": 340_000_000, "volume_24h_usd": 890_000_000}, {"pair": "SOL/USDT", "dex": "Orca", "liquidity_usd": 210_000_000, "volume_24h_usd": 560_000_000}], "liquidity_score": 91.3},
    "cardano": {"dex_liquidity_usd": 120_000_000, "trading_volume_24h_usd": 380_000_000, "liquidity_depth": {"plus_2_pct_usd": 18_000_000, "minus_2_pct_usd": 15_000_000}, "impermanent_loss_risk": "MEDIUM", "major_dex_pairs": [{"pair": "ADA/USDT", "dex": "Minswap", "liquidity_usd": 45_000_000, "volume_24h_usd": 28_000_000}], "liquidity_score": 68.9},
    "polkadot": {"dex_liquidity_usd": 95_000_000, "trading_volume_24h_usd": 210_000_000, "liquidity_depth": {"plus_2_pct_usd": 14_000_000, "minus_2_pct_usd": 12_000_000}, "impermanent_loss_risk": "MEDIUM", "major_dex_pairs": [{"pair": "DOT/USDT", "dex": "HydraDX", "liquidity_usd": 38_000_000, "volume_24h_usd": 22_000_000}], "liquidity_score": 65.4},
    "chainlink": {"dex_liquidity_usd": 310_000_000, "trading_volume_24h_usd": 520_000_000, "liquidity_depth": {"plus_2_pct_usd": 48_000_000, "minus_2_pct_usd": 42_000_000}, "impermanent_loss_risk": "LOW", "major_dex_pairs": [{"pair": "LINK/ETH", "dex": "Uniswap V3", "liquidity_usd": 120_000_000, "volume_24h_usd": 85_000_000}, {"pair": "LINK/USDC", "dex": "Uniswap V3", "liquidity_usd": 78_000_000, "volume_24h_usd": 52_000_000}], "liquidity_score": 84.7},
    "aave": {"dex_liquidity_usd": 145_000_000, "trading_volume_24h_usd": 185_000_000, "liquidity_depth": {"plus_2_pct_usd": 22_000_000, "minus_2_pct_usd": 19_000_000}, "impermanent_loss_risk": "MEDIUM", "major_dex_pairs": [{"pair": "AAVE/ETH", "dex": "Uniswap V3", "liquidity_usd": 68_000_000, "volume_24h_usd": 42_000_000}], "liquidity_score": 76.2},
    "lido": {"dex_liquidity_usd": 420_000_000, "trading_volume_24h_usd": 95_000_000, "liquidity_depth": {"plus_2_pct_usd": 65_000_000, "minus_2_pct_usd": 58_000_000}, "impermanent_loss_risk": "MEDIUM", "major_dex_pairs": [{"pair": "stETH/ETH", "dex": "Curve", "liquidity_usd": 320_000_000, "volume_24h_usd": 45_000_000}], "liquidity_score": 79.8},
    "arbitrum": {"dex_liquidity_usd": 180_000_000, "trading_volume_24h_usd": 290_000_000, "liquidity_depth": {"plus_2_pct_usd": 28_000_000, "minus_2_pct_usd": 24_000_000}, "impermanent_loss_risk": "MEDIUM", "major_dex_pairs": [{"pair": "ARB/ETH", "dex": "Uniswap V3", "liquidity_usd": 72_000_000, "volume_24h_usd": 48_000_000}], "liquidity_score": 72.1},
    "optimism": {"dex_liquidity_usd": 95_000_000, "trading_volume_24h_usd": 145_000_000, "liquidity_depth": {"plus_2_pct_usd": 15_000_000, "minus_2_pct_usd": 12_000_000}, "impermanent_loss_risk": "MEDIUM", "major_dex_pairs": [{"pair": "OP/ETH", "dex": "Uniswap V3", "liquidity_usd": 42_000_000, "volume_24h_usd": 28_000_000}], "liquidity_score": 67.5},
    "dydx": {"dex_liquidity_usd": 65_000_000, "trading_volume_24h_usd": 380_000_000, "liquidity_depth": {"plus_2_pct_usd": 10_000_000, "minus_2_pct_usd": 8_500_000}, "impermanent_loss_risk": "HIGH", "major_dex_pairs": [{"pair": "DYDX/USDC", "dex": "dYdX DEX", "liquidity_usd": 45_000_000, "volume_24h_usd": 280_000_000}], "liquidity_score": 61.3},
    "ftx-token": {"dex_liquidity_usd": 1_200_000, "trading_volume_24h_usd": 850_000, "liquidity_depth": {"plus_2_pct_usd": 180_000, "minus_2_pct_usd": 120_000}, "impermanent_loss_risk": "HIGH", "major_dex_pairs": [{"pair": "FTT/USDT", "dex": "Uniswap V3", "liquidity_usd": 450_000, "volume_24h_usd": 280_000}], "liquidity_score": 8.5},
    "terra-luna": {"dex_liquidity_usd": 50_000, "trading_volume_24h_usd": 12_000, "liquidity_depth": {"plus_2_pct_usd": 5_000, "minus_2_pct_usd": 3_000}, "impermanent_loss_risk": "HIGH", "major_dex_pairs": [], "liquidity_score": 2.1},
    "safemoon": {"dex_liquidity_usd": 280_000, "trading_volume_24h_usd": 45_000, "liquidity_depth": {"plus_2_pct_usd": 28_000, "minus_2_pct_usd": 18_000}, "impermanent_loss_risk": "HIGH", "major_dex_pairs": [{"pair": "SFM/BNB", "dex": "PancakeSwap", "liquidity_usd": 180_000, "volume_24h_usd": 32_000}], "liquidity_score": 5.8},
}

_CRYPTO_WHALE_DATA: dict[str, dict] = {
    "bitcoin": {"top_10_holders": [{"rank": 1, "address": "0x34xk9...satoshi", "balance_pct": 5.2, "label": "Satoshi Nakamoto (est.)"}, {"rank": 2, "address": "0xBE0e...binance7", "balance_pct": 3.8, "label": "Binance Cold Wallet"}, {"rank": 3, "address": "0x28c6...binance", "balance_pct": 2.9, "label": "Binance Hot Wallet"}], "whale_concentration_pct": 15.4, "recent_whale_movements": [{"direction": "BUY", "amount_usd": 45_000_000, "timestamp": "2026-05-28T14:00:00Z"}, {"direction": "SELL", "amount_usd": 12_000_000, "timestamp": "2026-05-27T09:30:00Z"}], "accumulation_distribution_signal": "ACCUMULATION"},
    "ethereum": {"top_10_holders": [{"rank": 1, "address": "0x0000...deposit", "balance_pct": 26.8, "label": "ETH2 Deposit Contract"}, {"rank": 2, "address": "0xBE0e...binance", "balance_pct": 3.2, "label": "Binance Cold Wallet"}, {"rank": 3, "address": "0xC02a...wrapped", "balance_pct": 2.8, "label": "Wrapped ETH Contract"}], "whale_concentration_pct": 38.5, "recent_whale_movements": [{"direction": "BUY", "amount_usd": 28_000_000, "timestamp": "2026-05-29T10:00:00Z"}], "accumulation_distribution_signal": "ACCUMULATION"},
    "uniswap": {"top_10_holders": [{"rank": 1, "address": "0x1a9c...treasury", "balance_pct": 18.0, "label": "Uniswap Treasury"}, {"rank": 2, "address": "0x4b4e...a16z", "balance_pct": 5.4, "label": "a16z Wallet"}, {"rank": 3, "address": "0x7f0e...paradigm", "balance_pct": 4.1, "label": "Paradigm"}], "whale_concentration_pct": 42.3, "recent_whale_movements": [{"direction": "SELL", "amount_usd": 8_500_000, "timestamp": "2026-05-26T16:00:00Z"}], "accumulation_distribution_signal": "DISTRIBUTION"},
    "solana": {"top_10_holders": [{"rank": 1, "address": "0x9a3f...foundation", "balance_pct": 12.5, "label": "Solana Foundation"}, {"rank": 2, "address": "0x6d2e...labs", "balance_pct": 8.3, "label": "Solana Labs"}], "whale_concentration_pct": 32.1, "recent_whale_movements": [{"direction": "BUY", "amount_usd": 15_000_000, "timestamp": "2026-05-28T11:00:00Z"}], "accumulation_distribution_signal": "ACCUMULATION"},
    "cardano": {"top_10_holders": [{"rank": 1, "address": "addr1...iohk", "balance_pct": 8.2, "label": "IOHK Treasury"}, {"rank": 2, "address": "addr1...emurgo", "balance_pct": 5.1, "label": "Emurgo"}], "whale_concentration_pct": 22.8, "recent_whale_movements": [{"direction": "BUY", "amount_usd": 3_200_000, "timestamp": "2026-05-27T08:00:00Z"}], "accumulation_distribution_signal": "NEUTRAL"},
    "polkadot": {"top_10_holders": [{"rank": 1, "address": "15oF4...w3f", "balance_pct": 11.5, "label": "Web3 Foundation"}, {"rank": 2, "address": "14Gjs...parity", "balance_pct": 6.2, "label": "Parity Technologies"}], "whale_concentration_pct": 28.4, "recent_whale_movements": [{"direction": "SELL", "amount_usd": 2_800_000, "timestamp": "2026-05-25T14:00:00Z"}], "accumulation_distribution_signal": "DISTRIBUTION"},
    "chainlink": {"top_10_holders": [{"rank": 1, "address": "0x5589...treasury", "balance_pct": 35.0, "label": "Chainlink Treasury"}, {"rank": 2, "address": "0x7c83...team", "balance_pct": 8.5, "label": "Team Wallet"}], "whale_concentration_pct": 52.8, "recent_whale_movements": [{"direction": "BUY", "amount_usd": 5_600_000, "timestamp": "2026-05-29T07:00:00Z"}], "accumulation_distribution_signal": "ACCUMULATION"},
    "aave": {"top_10_holders": [{"rank": 1, "address": "0xec56...ecosystem", "balance_pct": 14.2, "label": "Aave Ecosystem Reserve"}, {"rank": 2, "address": "0x25f2...safety", "balance_pct": 6.8, "label": "Safety Module"}], "whale_concentration_pct": 34.6, "recent_whale_movements": [{"direction": "BUY", "amount_usd": 4_200_000, "timestamp": "2026-05-28T13:00:00Z"}], "accumulation_distribution_signal": "ACCUMULATION"},
    "lido": {"top_10_holders": [{"rank": 1, "address": "0x3e40...treasury", "balance_pct": 22.0, "label": "Lido DAO Treasury"}, {"rank": 2, "address": "0x4b4e...a16z", "balance_pct": 4.8, "label": "a16z Wallet"}], "whale_concentration_pct": 41.2, "recent_whale_movements": [{"direction": "SELL", "amount_usd": 6_100_000, "timestamp": "2026-05-27T15:00:00Z"}], "accumulation_distribution_signal": "DISTRIBUTION"},
    "arbitrum": {"top_10_holders": [{"rank": 1, "address": "0xf3fc...dao", "balance_pct": 42.8, "label": "Arbitrum DAO Treasury"}, {"rank": 2, "address": "0x2c8e...offchain", "balance_pct": 7.5, "label": "Offchain Labs"}], "whale_concentration_pct": 58.9, "recent_whale_movements": [{"direction": "SELL", "amount_usd": 9_400_000, "timestamp": "2026-05-26T12:00:00Z"}], "accumulation_distribution_signal": "DISTRIBUTION"},
    "optimism": {"top_10_holders": [{"rank": 1, "address": "0x2501...foundation", "balance_pct": 30.5, "label": "Optimism Foundation"}, {"rank": 2, "address": "0x4200...eco", "balance_pct": 8.9, "label": "Ecosystem Fund"}], "whale_concentration_pct": 52.1, "recent_whale_movements": [{"direction": "SELL", "amount_usd": 7_200_000, "timestamp": "2026-05-25T10:00:00Z"}], "accumulation_distribution_signal": "DISTRIBUTION"},
    "dydx": {"top_10_holders": [{"rank": 1, "address": "0xb9d4...community", "balance_pct": 26.4, "label": "Community Treasury"}, {"rank": 2, "address": "0x68c5...investors", "balance_pct": 12.1, "label": "Investor Pool"}], "whale_concentration_pct": 55.3, "recent_whale_movements": [{"direction": "SELL", "amount_usd": 3_800_000, "timestamp": "2026-05-24T18:00:00Z"}], "accumulation_distribution_signal": "DISTRIBUTION"},
    "ftx-token": {"top_10_holders": [{"rank": 1, "address": "0xa7ef...estate", "balance_pct": 45.2, "label": "FTX Bankruptcy Estate"}, {"rank": 2, "address": "0x2faf...alameda", "balance_pct": 18.7, "label": "Alameda Research (frozen)"}], "whale_concentration_pct": 78.4, "recent_whale_movements": [], "accumulation_distribution_signal": "NEUTRAL"},
    "terra-luna": {"top_10_holders": [{"rank": 1, "address": "terra1...lfg", "balance_pct": 28.5, "label": "Luna Foundation Guard (frozen)"}, {"rank": 2, "address": "terra1...kwon", "balance_pct": 15.2, "label": "Do Kwon (frozen)"}], "whale_concentration_pct": 62.8, "recent_whale_movements": [], "accumulation_distribution_signal": "NEUTRAL"},
    "safemoon": {"top_10_holders": [{"rank": 1, "address": "0x8076...lp", "balance_pct": 32.1, "label": "Locked LP"}, {"rank": 2, "address": "0x9a7b...dev", "balance_pct": 15.8, "label": "Dev Wallet (frozen)"}], "whale_concentration_pct": 68.5, "recent_whale_movements": [], "accumulation_distribution_signal": "NEUTRAL"},
}

_CRYPTO_DEFI_DATA: dict[str, dict] = {
    "bitcoin": {"tvl_usd": 1_200_000_000, "apy_pct": 1.2, "protocol_revenue_30d_usd": 890_000_000, "audit_status": {"audited": True, "auditor": "Community Reviewed", "last_audit_date": "2026-01-01", "critical_findings": 0}, "exploit_history": []},
    "ethereum": {"tvl_usd": 58_700_000_000, "apy_pct": 3.8, "protocol_revenue_30d_usd": 1_450_000_000, "audit_status": {"audited": True, "auditor": "Multiple (EF, Trail of Bits)", "last_audit_date": "2026-03-15", "critical_findings": 0}, "exploit_history": []},
    "uniswap": {"tvl_usd": 5_200_000_000, "apy_pct": 12.5, "protocol_revenue_30d_usd": 78_000_000, "audit_status": {"audited": True, "auditor": "Trail of Bits", "last_audit_date": "2026-02-20", "critical_findings": 0}, "exploit_history": []},
    "solana": {"tvl_usd": 8_900_000_000, "apy_pct": 6.8, "protocol_revenue_30d_usd": 42_000_000, "audit_status": {"audited": True, "auditor": "Kudelski Security", "last_audit_date": "2026-01-10", "critical_findings": 0}, "exploit_history": [{"date": "2022-08-02", "type": "Slope Wallet Exploit", "loss_usd": 8_000_000, "recovered": False}]},
    "cardano": {"tvl_usd": 420_000_000, "apy_pct": 4.2, "protocol_revenue_30d_usd": 2_800_000, "audit_status": {"audited": True, "auditor": "Tweag", "last_audit_date": "2025-12-01", "critical_findings": 0}, "exploit_history": []},
    "polkadot": {"tvl_usd": 1_200_000_000, "apy_pct": 14.5, "protocol_revenue_30d_usd": 5_600_000, "audit_status": {"audited": True, "auditor": "SRLabs", "last_audit_date": "2025-11-15", "critical_findings": 0}, "exploit_history": []},
    "chainlink": {"tvl_usd": 18_500_000_000, "apy_pct": 5.2, "protocol_revenue_30d_usd": 15_000_000, "audit_status": {"audited": True, "auditor": "CertiK", "last_audit_date": "2026-04-01", "critical_findings": 0}, "exploit_history": []},
    "aave": {"tvl_usd": 12_800_000_000, "apy_pct": 8.4, "protocol_revenue_30d_usd": 32_000_000, "audit_status": {"audited": True, "auditor": "OpenZeppelin", "last_audit_date": "2026-03-10", "critical_findings": 0}, "exploit_history": [{"date": "2023-11-12", "type": "Flash Loan Governance Attack", "loss_usd": 1_600_000, "recovered": True}]},
    "lido": {"tvl_usd": 14_500_000_000, "apy_pct": 3.9, "protocol_revenue_30d_usd": 28_000_000, "audit_status": {"audited": True, "auditor": "Quantstamp", "last_audit_date": "2026-02-15", "critical_findings": 0}, "exploit_history": []},
    "arbitrum": {"tvl_usd": 3_200_000_000, "apy_pct": 5.8, "protocol_revenue_30d_usd": 8_500_000, "audit_status": {"audited": True, "auditor": "Trail of Bits", "last_audit_date": "2026-01-20", "critical_findings": 0}, "exploit_history": []},
    "optimism": {"tvl_usd": 1_800_000_000, "apy_pct": 6.2, "protocol_revenue_30d_usd": 5_200_000, "audit_status": {"audited": True, "auditor": "OpenZeppelin", "last_audit_date": "2025-12-10", "critical_findings": 1}, "exploit_history": [{"date": "2022-02-03", "type": "Token Bridge Bug", "loss_usd": 0, "recovered": True}]},
    "dydx": {"tvl_usd": 340_000_000, "apy_pct": 18.5, "protocol_revenue_30d_usd": 12_000_000, "audit_status": {"audited": True, "auditor": "Consensys Diligence", "last_audit_date": "2025-10-05", "critical_findings": 0}, "exploit_history": []},
    "ftx-token": {"tvl_usd": 0, "apy_pct": 0.0, "protocol_revenue_30d_usd": 0, "audit_status": {"audited": False, "auditor": None, "last_audit_date": None, "critical_findings": 0}, "exploit_history": [{"date": "2022-11-11", "type": "Exchange Collapse / Misappropriation", "loss_usd": 8_000_000_000, "recovered": False}]},
    "terra-luna": {"tvl_usd": 0, "apy_pct": 0.0, "protocol_revenue_30d_usd": 0, "audit_status": {"audited": False, "auditor": None, "last_audit_date": None, "critical_findings": 0}, "exploit_history": [{"date": "2022-05-09", "type": "Algorithmic Stablecoin Death Spiral", "loss_usd": 40_000_000_000, "recovered": False}]},
    "safemoon": {"tvl_usd": 0, "apy_pct": 0.0, "protocol_revenue_30d_usd": 0, "audit_status": {"audited": True, "auditor": "CertiK", "last_audit_date": "2021-05-10", "critical_findings": 8}, "exploit_history": [{"date": "2023-03-28", "type": "LP Drain / Rug Pull", "loss_usd": 8_900_000, "recovered": False}]},
}


def _enrich_companies(companies: list[dict]) -> None:
    """Add salary_data and hiring_data fields to company documents."""
    for company in companies:
        slug = company.get("profile_slug", "")
        company["salary_data"] = _COMPANY_SALARY_DATA.get(slug, {
            "salary_ranges": {
                "junior": {"min": 45000, "max": 60000, "currency": "EUR"},
                "mid": {"min": 60000, "max": 80000, "currency": "EUR"},
                "senior": {"min": 85000, "max": 120000, "currency": "EUR"},
            },
            "median_salary": 70000,
            "salary_vs_industry_avg_pct": 0.0,
            "benefits_summary": {"health_insurance": True, "remote_work": False, "stock_options": False, "pension_plan": True, "bonus_structure": "none", "vacation_days": 25},
        })
        company["hiring_data"] = _COMPANY_HIRING_DATA.get(slug, {
            "open_positions": 0, "growth_rate_pct": 0.0, "trending_roles": [],
            "remote_vs_office": {"remote_pct": 0.0, "hybrid_pct": 0.0, "office_pct": 100.0},
            "diversity_score": 50.0, "avg_time_to_hire_days": 30,
        })


def _enrich_crypto_projects(projects: list[dict]) -> None:
    """Add liquidity_data, whale_data, and defi_data fields to crypto documents."""
    for project in projects:
        slug = project.get("slug", "")
        project["liquidity_data"] = _CRYPTO_LIQUIDITY_DATA.get(slug, {
            "dex_liquidity_usd": 0, "trading_volume_24h_usd": 0,
            "liquidity_depth": {"plus_2_pct_usd": 0, "minus_2_pct_usd": 0},
            "impermanent_loss_risk": "HIGH", "major_dex_pairs": [], "liquidity_score": 0.0,
        })
        project["whale_data"] = _CRYPTO_WHALE_DATA.get(slug, {
            "top_10_holders": [], "whale_concentration_pct": 0.0,
            "recent_whale_movements": [], "accumulation_distribution_signal": "NEUTRAL",
        })
        project["defi_data"] = _CRYPTO_DEFI_DATA.get(slug, {
            "tvl_usd": 0, "apy_pct": 0.0, "protocol_revenue_30d_usd": 0,
            "audit_status": {"audited": False, "auditor": None, "last_audit_date": None, "critical_findings": 0},
            "exploit_history": [],
        })


# ═══════════════════════════════════════════════════════════════════════════
# Seeding Logic
# ═══════════════════════════════════════════════════════════════════════════

def _connect() -> MongoClient:
    """Create and verify a MongoDB Atlas connection."""
    uri = os.getenv("MONGODB_CONNECTION_STRING")
    if not uri:
        log.error("MONGODB_CONNECTION_STRING environment variable is not set.")
        log.error("Add it to your .env file or export it in the shell.")
        sys.exit(1)

    log.info("Connecting to MongoDB Atlas …")
    client = MongoClient(uri, serverSelectionTimeoutMS=10_000)

    # Force a connection check
    try:
        client.admin.command("ping")
    except ConnectionFailure as exc:
        log.error("Failed to connect to MongoDB Atlas: %s", exc)
        sys.exit(1)

    log.info("✅ Connected successfully.")
    return client


def _drop_collections(db) -> None:
    """Drop all target collections."""
    collections = ["companies", "reviews", "crypto_projects", "wallets", "investigations", "audit_log"]
    for name in collections:
        db.drop_collection(name)
        log.info("  🗑  Dropped collection: %s", name)


def _seed_companies(db) -> int:
    """Insert company documents (enriched with salary + hiring data)."""
    _enrich_companies(COMPANIES)
    coll = db["companies"]
    coll.insert_many(COMPANIES)
    return len(COMPANIES)


def _seed_reviews(db) -> int:
    """Insert review documents."""
    coll = db["reviews"]
    coll.insert_many(REVIEWS)
    return len(REVIEWS)


def _seed_crypto_projects(db) -> int:
    """Insert crypto project documents (enriched with liquidity + whale + DeFi data)."""
    _enrich_crypto_projects(CRYPTO_PROJECTS)
    coll = db["crypto_projects"]
    coll.insert_many(CRYPTO_PROJECTS)
    return len(CRYPTO_PROJECTS)


def _seed_wallets(db) -> int:
    """Insert wallet documents."""
    coll = db["wallets"]
    coll.insert_many(WALLETS)
    return len(WALLETS)


def _create_empty_collections(db) -> None:
    """Create empty collections for agent-populated data."""
    for name in ["investigations", "audit_log"]:
        db.create_collection(name)
        log.info("  📂 Created empty collection: %s", name)


def _create_indexes(db) -> None:
    """Create all required indexes."""
    log.info("Creating indexes …")

    # Companies
    db["companies"].create_index("profile_slug", unique=True, name="idx_profile_slug_unique")
    db["companies"].create_index([("company_name", TEXT)], name="idx_company_name_text")
    log.info("  🔑 companies: profile_slug (unique), company_name (text)")

    # Reviews
    db["reviews"].create_index(
        [("company_slug", ASCENDING), ("date", DESCENDING)],
        name="idx_company_slug_date",
    )
    log.info("  🔑 reviews: company_slug + date")

    # Crypto projects
    db["crypto_projects"].create_index("slug", unique=True, name="idx_slug_unique")
    db["crypto_projects"].create_index(
        [("name", TEXT), ("symbol", TEXT)],
        name="idx_name_symbol_text",
    )
    log.info("  🔑 crypto_projects: slug (unique), name+symbol (text)")

    # Wallets
    db["wallets"].create_index("address", unique=True, name="idx_address_unique")
    log.info("  🔑 wallets: address (unique)")

    # Investigations
    db["investigations"].create_index(
        [("timestamp", DESCENDING)],
        name="idx_timestamp",
    )
    log.info("  🔑 investigations: timestamp")

    # Audit log
    db["audit_log"].create_index(
        [("timestamp", DESCENDING)],
        name="idx_audit_timestamp",
    )
    log.info("  🔑 audit_log: timestamp")


def _print_summary(counts: dict[str, int]) -> None:
    """Print a nice summary table."""
    print()
    print("═" * 52)
    print("  🛡️  Vartovii Trust Agent — MongoDB Seed Summary")
    print("═" * 52)
    total = 0
    for collection, count in counts.items():
        total += count
        status = f"{count} documents" if count > 0 else "empty (ready)"
        print(f"  {collection:<22} {status}")
    print("─" * 52)
    print(f"  {'Total documents':<22} {total}")
    print(f"  {'Database':<22} {DATABASE_NAME}")
    print("═" * 52)
    print()


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed Vartovii MongoDB Atlas with demo data.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Drop existing collections before seeding.",
    )
    args = parser.parse_args()

    client = _connect()
    db = client[DATABASE_NAME]

    # Check if collections already have data
    existing = [
        name
        for name in ["companies", "reviews", "crypto_projects", "wallets"]
        if name in db.list_collection_names() and db[name].count_documents({}) > 0
    ]

    if existing and not args.force:
        log.error(
            "Collections already contain data: %s. "
            "Use --force to drop and re-seed.",
            ", ".join(existing),
        )
        sys.exit(1)

    if args.force:
        log.info("--force: dropping existing collections …")
        _drop_collections(db)

    # Seed data
    counts: dict[str, int] = {}

    log.info("Seeding companies …")
    counts["companies"] = _seed_companies(db)

    log.info("Seeding reviews …")
    counts["reviews"] = _seed_reviews(db)

    log.info("Seeding crypto_projects …")
    counts["crypto_projects"] = _seed_crypto_projects(db)

    log.info("Seeding wallets …")
    counts["wallets"] = _seed_wallets(db)

    log.info("Creating empty collections …")
    _create_empty_collections(db)
    counts["investigations"] = 0
    counts["audit_log"] = 0

    _create_indexes(db)

    _print_summary(counts)
    log.info("🎉 Seeding complete!")

    client.close()


if __name__ == "__main__":
    main()
