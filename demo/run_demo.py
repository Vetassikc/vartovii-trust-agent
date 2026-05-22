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

# Ensure GOOGLE_API_KEY is set
if not os.getenv("GOOGLE_API_KEY"):
    print("❌ Error: GOOGLE_API_KEY not set.")
    print("   Get your key at: https://aistudio.google.com/apikey")
    print("   Then: export GOOGLE_API_KEY=your_key_here")
    sys.exit(1)

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

    print(f"🤖 Agent Response:\n")
    print(final_response)
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
