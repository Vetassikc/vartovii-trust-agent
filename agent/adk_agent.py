"""
Vartovii Trust Intelligence Agent — ADK Multi-Agent Architecture

Root Orchestrator delegates to specialized sub-agents:
  • Corporate Agent — employer analytics (Trust Score, reviews, comparisons)
  • Crypto Agent — crypto intelligence + on-chain forensics
  • OSINT Agent — real-time web research via Google Search Grounding

This is the core agent definition extracted from the production Vartovii platform
(sentryanalytic.com). In production, this system has been live since March 25, 2026,
deployed on Google Cloud Run with ADK_ENABLED=true.

Usage:
    from agent.adk_agent import root_agent

    # Run with InMemoryRunner:
    from google.adk.runners import InMemoryRunner
    runner = InMemoryRunner(agent=root_agent, app_name="vartovii")

    # Or use the built-in ADK dev interface:
    # $ adk web agent/
"""

import logging

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.tools.google_search_tool import GoogleSearchTool

from .config import AIConfig
from .prompts.adk import (
    CORPORATE_AGENT_INSTRUCTION,
    CRYPTO_AGENT_INSTRUCTION,
    ORCHESTRATOR_AGENT_INSTRUCTION,
    OSINT_AGENT_INSTRUCTION,
)

# Import tool functions
from .tools.corporate_tools import (
    compare_companies,
    get_company_reviews,
    get_trust_score,
    get_vacancy_intelligence,
    list_companies,
    search_company,
)
from .tools.crypto_tools import (
    check_wallet,
    get_contract_info,
    get_crypto_trust_score,
    get_token_holders,
    get_transaction_history,
    search_crypto_projects,
)

logger = logging.getLogger(__name__)

# ============ Sub-Agent: Corporate Intelligence ============

corporate_agent = LlmAgent(
    name="corporate_agent",
    model=AIConfig.ADK_MODEL,
    description=(
        "Expert in employer analytics. Use this agent for questions about "
        "companies as employers: Trust Score, employee reviews, comparisons, "
        "vacancy intelligence, top employers ranking."
    ),
    instruction=AIConfig.get_adk_instruction("corporate", CORPORATE_AGENT_INSTRUCTION),
    tools=[
        FunctionTool(search_company),
        FunctionTool(get_trust_score),
        FunctionTool(list_companies),
        FunctionTool(compare_companies),
        FunctionTool(get_company_reviews),
        FunctionTool(get_vacancy_intelligence),
    ],
)

# ============ Sub-Agent: Crypto Intelligence ============

crypto_agent = LlmAgent(
    name="crypto_agent",
    model=AIConfig.ADK_MODEL,
    description=(
        "Expert in cryptocurrency analysis and on-chain forensics. Use this "
        "agent for crypto project data (Trust Score, tokenomics, investors), "
        "wallet investigations, transaction analysis, token holder distribution."
    ),
    instruction=AIConfig.get_adk_instruction("crypto", CRYPTO_AGENT_INSTRUCTION),
    tools=[
        FunctionTool(search_crypto_projects),
        FunctionTool(get_crypto_trust_score),
        FunctionTool(check_wallet),
        FunctionTool(get_transaction_history),
        FunctionTool(get_token_holders),
        FunctionTool(get_contract_info),
    ],
)

# ============ Sub-Agent: OSINT (Web Research) ============

osint_agent = LlmAgent(
    name="osint_agent",
    model=AIConfig.ADK_MODEL,
    description=(
        "Expert in real-time OSINT web research. Use this agent when "
        "information is NOT in the database and requires Google Search: "
        "founder background checks, recent company news, domain verification, "
        "crypto project research not yet analyzed, industry trends."
    ),
    instruction=AIConfig.get_adk_instruction("osint", OSINT_AGENT_INSTRUCTION),
    tools=[
        GoogleSearchTool(),
    ],
)

# ============ Root Orchestrator ============

root_agent = LlmAgent(
    name="vartovii_orchestrator",
    model=AIConfig.ADK_MODEL,
    description="Vartovii AI — Trust Intelligence Platform assistant",
    instruction=AIConfig.get_adk_instruction("orchestrator", ORCHESTRATOR_AGENT_INSTRUCTION),
    sub_agents=[corporate_agent, crypto_agent, osint_agent],
    tools=[],  # Orchestrator delegates only — no direct tools
)

logger.info(
    "🤖 Vartovii ADK Agent initialized: root + 3 sub-agents "
    "(corporate: 6 tools, crypto: 6 tools, osint: Google Search)"
)
