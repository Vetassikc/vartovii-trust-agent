"""
Demo runner for the Vartovii Trust Intelligence Agent.

This script demonstrates the multi-agent ADK system in action,
showing how the root orchestrator delegates to specialized sub-agents.

Usage:
    python -m demo.run_demo

    # Or use the ADK web interface:
    adk web agent/
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Warn if GOOGLE_API_KEY is not set, but allow fallback to Application Default Credentials (ADC)
if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and not os.path.exists(os.path.expanduser("~/.config/gcloud/application_default_credentials.json")):
    print("❌ Error: Neither GOOGLE_API_KEY nor Google Application Default Credentials (ADC) are set.")
    print("   Get your key at: https://aistudio.google.com/apikey")
    print("   Or run: gcloud auth application-default login")
    sys.exit(1)
elif not os.getenv("GOOGLE_API_KEY"):
    print("ℹ️  Note: GOOGLE_API_KEY not set. Using Google Application Default Credentials (ADC) for authentication.")

from google.adk.runners import InMemoryRunner
from google.genai import types

from agent.adk_agent import root_agent


DEMO_SCENARIOS = [
    {
        "title": "🏢 Corporate Trust Assessment",
        "query": "Analyze SAP as an employer. What's their Trust Score?",
        "description": "Routes to Corporate Agent → search_company → get_trust_score",
    },
    {
        "title": "🪙 Crypto Project Analysis",
        "query": "Give me the full trust assessment for Uniswap including security score",
        "description": "Routes to Crypto Agent → search_crypto_projects → get_crypto_trust_score",
    },
    {
        "title": "🏢 vs 🏢 Company Comparison",
        "query": "Compare BMW and SAP as employers",
        "description": "Routes to Corporate Agent → compare_companies",
    },
    {
        "title": "🔍 OSINT Investigation",
        "query": "Who is the founder of Monad Labs? What is their background?",
        "description": "Routes to OSINT Agent → Google Search",
    },
    {
        "title": "🔗 Blockchain Forensics",
        "query": "Check the wallet 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        "description": "Routes to Crypto Agent → check_wallet",
    },
]


async def run_demo(scenario_index: int = 0):
    """Run a single demo scenario."""
    scenario = DEMO_SCENARIOS[scenario_index]

    print(f"\n{'='*70}")
    print(f"  {scenario['title']}")
    print(f"  {scenario['description']}")
    print(f"{'='*70}")
    print(f"\n📝 Query: \"{scenario['query']}\"\n")
    print("⏳ Processing through multi-agent pipeline...\n")

    MOCK_RESPONSES = {
        0: (
            "🏢 **Corporate Agent** (delegated by Orchestrator):\n\n"
            "**SAP SE (Employer Trust Assessment)**\n"
            "- **Trust Score:** 74/100 (MEDIUM Risk)\n"
            "- **Review Analysis:** Based on 1,200+ employee reviews, common pros include high career development potential and competitive compensation. Common cons center on rigid corporate structures.\n"
            "- **Ghost Vacancy Risk:** Low. out of 50 active listings, 12 show signs of being stagnant vacancies (stale for 45+ days).\n"
            "- **Pillar Scores:** Leadership: 72/100 | Compensation: 78/100 | Culture: 70/100 | Development: 75/100"
        ),
        1: (
            "🪙 **Crypto Agent** (delegated by Orchestrator):\n\n"
            "**Uniswap (UNI) Project Audit**\n"
            "- **Overall Trust Score:** 78/100 (LOW Risk)\n"
            "- **Security Audit:** Codebase verified. Contract bytecode matches compiler standard version 0.8.20. Main pools (v3) have $4.2B TVL.\n"
            "- **Token Distribution:** Smart contract has low concentration risk in dev-owned wallets, but treasury hold remains substantial (34% of supply locked in governance contract).\n"
            "- **Development Health:** High active commits (34 developers contributing over the last 30 days)."
        ),
        2: (
            "🏢 **Corporate Agent** (delegated by Orchestrator):\n\n"
            "**Employer Comparison: BMW Group vs SAP SE**\n"
            "- **Winner:** BMW Group (Trust Score: 82/100) vs SAP SE (Trust Score: 74/100)\n"
            "- **Compensation:** BMW scores higher (85/100) compared to SAP (78/100).\n"
            "- **Work-Life Balance:** BMW scored 78/100, while SAP scored 70/100.\n"
            "- **Recommendation:** For employees prioritizing stability and premium work-life balance, BMW is the recommended employer. SAP remains highly competitive for software-oriented growth."
        ),
        3: (
            "🔍 **OSINT Agent** (delegated by Orchestrator via Google Search Grounding):\n\n"
            "**Monad Labs Founder Profile**\n"
            "- **Co-Founder:** Keone Hon\n"
            "- **Background:** Keone was previously a quantitative developer at Jump Trading (8 years tenure), specializing in high-frequency trading engines.\n"
            "- **Project Background:** He founded Monad Labs in 2022 to build Monad, a high-performance EVM-equivalent Layer 1 blockchain optimized for parallel execution."
        ),
        4: (
            "🪙 **Crypto Agent** (delegated by Orchestrator):\n\n"
            "**Blockchain Forensics: Wallet 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045**\n"
            "- **Address Owner:** Vitalik Buterin (Labeled: vitalik.eth)\n"
            "- **ETH Balance:** 1,247.34 ETH (~$3.74 Million USD)\n"
            "- **Transaction Activity:** 250+ transactions analyzed in past 30 days. High interaction with DeFi protocols (Uniswap v3, Gitcoin Safe, Base Bridge).\n"
            "- **Security Check:** Verified ownership signature. Wallet operates under standard high-security standards."
        ),
    }

    try:
        runner = InMemoryRunner(agent=root_agent, app_name="vartovii_demo")
        session = await runner.session_service.create_session(
            app_name="vartovii_demo", user_id="demo_user"
        )

        user_msg = types.Content(
            role="user",
            parts=[types.Part(text=scenario["query"])],
        )

        final_response = ""
        async for event in runner.run_async(
            user_id="demo_user",
            session_id=session.id,
            new_message=user_msg,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_response += part.text
        
        print(f"🤖 Agent Response (Live API):\n")
        print(final_response)

    except Exception as e:
        print(f"ℹ️ Note: Live API connection is unavailable ({type(e).__name__}).")
        print("🛡️  Falling back to Local Resilience Simulation (Graceful Degradation Demonstration):\n")
        print(f"🤖 Agent Response (Simulated):\n")
        print(MOCK_RESPONSES.get(scenario_index, "No data available."))
    
    print(f"\n{'='*70}\n")


async def run_all_demos():
    """Run all demo scenarios sequentially."""
    print("\n" + "🚀" * 35)
    print("  VARTOVII TRUST INTELLIGENCE AGENT — DEMO")
    print("  Powered by Google ADK + Gemini")
    print("🚀" * 35 + "\n")

    for i, scenario in enumerate(DEMO_SCENARIOS):
        await run_demo(i)
        if i < len(DEMO_SCENARIOS) - 1:
            print("⏭️  Next scenario in 2 seconds...\n")
            await asyncio.sleep(2)

    print("\n✅ All demo scenarios completed!")
    print("📊 Live platform: https://sentryanalytic.com")
    print("📖 Documentation: https://docs.sentryanalytic.com")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            idx = int(sys.argv[1])
            asyncio.run(run_demo(idx))
        except (ValueError, IndexError):
            print(f"Usage: python -m demo.run_demo [0-{len(DEMO_SCENARIOS)-1}]")
    else:
        asyncio.run(run_all_demos())
