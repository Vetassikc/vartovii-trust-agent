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
    """Insert company documents."""
    coll = db["companies"]
    coll.insert_many(COMPANIES)
    return len(COMPANIES)


def _seed_reviews(db) -> int:
    """Insert review documents."""
    coll = db["reviews"]
    coll.insert_many(REVIEWS)
    return len(REVIEWS)


def _seed_crypto_projects(db) -> int:
    """Insert crypto project documents."""
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
