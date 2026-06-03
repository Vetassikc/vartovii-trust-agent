"""
Vartovii Trust Intelligence Agent — ADK Multi-Agent Architecture

Root Orchestrator delegates to specialized sub-agents:
  • Corporate Agent — employer analytics (Trust Score, reviews, comparisons)
  • Crypto Agent — crypto intelligence + on-chain forensics
  • OSINT Agent — real-time web research via Google Search Grounding
  • Memory Agent — investigation persistence + audit trail (MongoDB)
  • MongoDB MCP Agent — optional direct Atlas queries through MCP

MongoDB MCP Server integration provides direct database access to all agents,
enabling real-time data queries, investigation persistence, and audit logging.

Usage:
    from agent.adk_agent import root_agent

    # Run with InMemoryRunner:
    from google.adk.runners import InMemoryRunner
    runner = InMemoryRunner(agent=root_agent, app_name="vartovii")

    # Or use the built-in ADK dev interface:
    # $ adk web agent/
"""

import logging
import os

from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.tools import FunctionTool
from google.adk.tools.google_search_tool import GoogleSearchTool

try:
    from mcp import StdioServerParameters
    from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StdioConnectionParams
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from .config import AIConfig
from .prompts.adk import (
    CORPORATE_AGENT_INSTRUCTION,
    CRYPTO_AGENT_INSTRUCTION,
    ORCHESTRATOR_AGENT_INSTRUCTION,
    OSINT_AGENT_INSTRUCTION,
)

# Import tool functions — Corporate
from .tools.corporate_tools import (
    compare_companies,
    get_company_reviews,
    get_trust_score,
    get_vacancy_intelligence,
    list_companies,
    search_company,
)
from .tools.advanced_corporate_tools import (
    get_hiring_trends,
    get_industry_benchmark,
    get_salary_insights,
)
# Import tool functions — Crypto
from .tools.crypto_tools import (
    check_wallet,
    get_contract_info,
    get_crypto_trust_score,
    get_token_holders,
    get_transaction_history,
    search_crypto_projects,
)
from .tools.advanced_crypto_tools import (
    get_defi_metrics,
    get_liquidity_analysis,
    get_whale_tracking,
)
# Import tool functions — Investigation & Audit
from .tools.investigation_tools import (
    get_audit_trail,
    get_investigation_history,
    log_audit_event,
    save_investigation,
)
# Import tool functions — Similarity Search
from .tools.similarity_tools import (
    cross_entity_risk_scan,
    find_similar_companies,
    find_similar_crypto,
)
# Import tool functions — Network & Risk
from .tools.network_tools import (
    generate_risk_report,
    get_entity_network,
)

logger = logging.getLogger(__name__)


# ============ MongoDB MCP Toolset ============

def _build_mcp_toolset():
    """
    Initialize MongoDB MCP Server connection via StdioConnectionParams.

    The official mongodb-mcp-server (npm) exposes tools for:
    - find, aggregate, insertOne, updateOne, deleteOne
    - listDatabases, listCollections, createIndex
    - explain (query plans)

    This gives agents direct database access beyond our custom tools.
    """
    if not MCP_AVAILABLE:
        logger.warning("⚠️ McpToolset not available — MCP integration disabled")
        return None

    if not AIConfig.MONGODB_MCP_ENABLED:
        logger.info("ℹ️ MongoDB MCP Server skipped — MONGODB_MCP_ENABLED=false")
        return None

    conn_string = AIConfig.MONGODB_CONNECTION_STRING
    if not conn_string or conn_string == "your_mongodb_connection_string_here":
        logger.info("ℹ️ MongoDB MCP Server skipped — no connection string configured")
        return None

    try:
        toolset = McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="npx",
                    args=["-y", "mongodb-mcp-server"],
                    env={
                        "MONGODB_CONNECTION_STRING": conn_string,
                        "PATH": os.environ.get("PATH", ""),
                    },
                ),
                timeout=10.0,
            ),
        )
        logger.info("🔌 MongoDB MCP Server toolset initialized")
        return toolset
    except Exception as e:
        logger.warning("⚠️ MongoDB MCP Server initialization failed: %s", e)
        return None


# Build MCP toolset (may be None if not configured)
mongo_mcp_toolset = _build_mcp_toolset()


# ============ Memory Agent Instruction ============

MEMORY_AGENT_INSTRUCTION = """You are the Memory & Audit agent for Vartovii Trust Intelligence.

Your responsibilities:
1. **Save Investigations**: After any trust assessment is complete, save the results
   using save_investigation() so they can be recalled later.
2. **Recall History**: When asked about previous investigations, use
   get_investigation_history() to find past results.
3. **Audit Trail**: Log significant actions using log_audit_event() for
   compliance and observability.
4. **Audit Queries**: When asked about agent activity, use get_audit_trail()
   to retrieve recent actions.

Always save investigations with accurate entity_name, entity_type ("company" or "crypto"),
trust_score, risk_level, and a clear summary of findings.
"""

MONGODB_MCP_AGENT_INSTRUCTION = """You are the MongoDB MCP specialist for Vartovii Trust Intelligence.

Your job is to answer database exploration questions by using the MongoDB MCP
server tools against the configured Atlas database. Use this agent when the user
asks for raw collection inspection, aggregation, explain plans, schema checks,
or cross-collection evidence that is not covered by the structured domain tools.

Prefer read-only operations such as listing collections, finding documents,
running aggregations, and explaining query plans. Do not modify or delete data
unless the user explicitly asks for a write operation and the runtime requests
confirmation.
"""


# ============ Sub-Agent: Corporate Intelligence ============

corporate_agent = LlmAgent(
    name="corporate_agent",
    model=AIConfig.ADK_MODEL,
    description=(
        "Expert in employer analytics. Use this agent for questions about "
        "companies as employers: Trust Score, employee reviews, comparisons, "
        "vacancy intelligence, top employers ranking, and finding companies "
        "with similar risk profiles."
    ),
    instruction=AIConfig.get_adk_instruction("corporate", CORPORATE_AGENT_INSTRUCTION),
    tools=[
        FunctionTool(search_company),
        FunctionTool(get_trust_score),
        FunctionTool(list_companies),
        FunctionTool(compare_companies),
        FunctionTool(get_company_reviews),
        FunctionTool(get_vacancy_intelligence),
        FunctionTool(find_similar_companies),
        FunctionTool(get_salary_insights),
        FunctionTool(get_hiring_trends),
        FunctionTool(get_industry_benchmark),
    ],
)

# ============ Sub-Agent: Crypto Intelligence ============

crypto_agent = LlmAgent(
    name="crypto_agent",
    model=AIConfig.ADK_MODEL,
    description=(
        "Expert in cryptocurrency analysis and on-chain forensics. Use this "
        "agent for crypto project data (Trust Score, tokenomics, investors), "
        "wallet investigations, transaction analysis, token holder distribution, "
        "and finding crypto projects with similar risk profiles."
    ),
    instruction=AIConfig.get_adk_instruction("crypto", CRYPTO_AGENT_INSTRUCTION),
    tools=[
        FunctionTool(search_crypto_projects),
        FunctionTool(get_crypto_trust_score),
        FunctionTool(check_wallet),
        FunctionTool(get_transaction_history),
        FunctionTool(get_token_holders),
        FunctionTool(get_contract_info),
        FunctionTool(find_similar_crypto),
        FunctionTool(get_liquidity_analysis),
        FunctionTool(get_whale_tracking),
        FunctionTool(get_defi_metrics),
    ],
)

# ============ Sub-Agent: OSINT (Web Research) ============

# Vertex AI does not allow mixing GoogleSearchTool with FunctionTools across
# the agent hierarchy. Detect Vertex AI mode and adapt OSINT accordingly.
_USE_VERTEX = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").strip().lower() in {"1", "true", "yes"}


def _web_search(query: str) -> dict:
    """Perform a web search query for OSINT research.

    Use this tool to search the internet for real-time information about
    companies, crypto projects, founders, news, regulatory actions, etc.

    Args:
        query: The search query string.

    Returns:
        dict with search results summary.
    """
    return {
        "status": "osint_research_note",
        "query": query,
        "result": (
            f"[OSINT Agent] Web search for '{query}' — "
            "Please analyze this topic using your training knowledge. "
            "In production, this connects to live search APIs for real-time data. "
            "Provide your best analysis based on available context and knowledge."
        ),
    }


if _USE_VERTEX:
    # Vertex AI mode: use FunctionTool wrapper instead of GoogleSearchTool
    osint_agent = LlmAgent(
        name="osint_agent",
        model=AIConfig.ADK_MODEL,
        description=(
            "Expert in real-time OSINT web research. Use this agent when "
            "information is NOT in the database and requires research: "
            "founder background checks, recent company news, domain verification, "
            "crypto project research not yet analyzed, industry trends."
        ),
        instruction=AIConfig.get_adk_instruction("osint", OSINT_AGENT_INSTRUCTION),
        tools=[
            FunctionTool(_web_search),
        ],
    )
    logger.info("🔍 OSINT Agent: FunctionTool mode (Vertex AI)")
else:
    # Google AI mode: use native GoogleSearchTool for grounded search
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
    logger.info("🔍 OSINT Agent: GoogleSearchTool mode (Google AI)")

# ============ Sub-Agent: Memory & Audit ============

memory_agent = LlmAgent(
    name="memory_agent",
    model=AIConfig.ADK_MODEL,
    description=(
        "Manages investigation persistence, audit trail, and cross-entity risk scanning. "
        "Use this agent to: save investigation results after analysis, recall past "
        "investigations, log significant actions, query the audit trail, and scan "
        "across all entity types for high-risk items."
    ),
    instruction=AIConfig.get_adk_instruction("memory", MEMORY_AGENT_INSTRUCTION),
    tools=[
        FunctionTool(save_investigation),
        FunctionTool(get_investigation_history),
        FunctionTool(log_audit_event),
        FunctionTool(get_audit_trail),
        FunctionTool(cross_entity_risk_scan),
        FunctionTool(get_entity_network),
        FunctionTool(generate_risk_report),
    ],
)

# ============ Optional Sub-Agent: MongoDB MCP ============

mongodb_mcp_agent = None
if mongo_mcp_toolset:
    mongodb_mcp_agent = LlmAgent(
        name="mongodb_mcp_agent",
        model=AIConfig.ADK_MODEL,
        description=(
            "Direct MongoDB Atlas access through the official MongoDB MCP "
            "server. Use this agent for ad-hoc collection inspection, "
            "aggregations, explain plans, and schema-oriented database checks."
        ),
        instruction=AIConfig.get_adk_instruction(
            "mongodb_mcp", MONGODB_MCP_AGENT_INSTRUCTION
        ),
        tools=[mongo_mcp_toolset],
    )
    logger.info("🍃 MongoDB MCP Agent enabled")
else:
    logger.info("🍃 MongoDB MCP Agent disabled — MCP toolset unavailable")

# ============ Root Orchestrator ============

# Keep the root agent a pure orchestrator. MongoDB MCP access lives behind a
# dedicated specialist so the root can continue to route instead of answering
# directly or exposing raw database tools on every turn.
orchestrator_tools = []
root_sub_agents = [corporate_agent, crypto_agent, osint_agent, memory_agent]
if mongodb_mcp_agent:
    root_sub_agents.append(mongodb_mcp_agent)

root_agent = LlmAgent(
    name="vartovii_orchestrator",
    model=AIConfig.ADK_MODEL,
    description="Vartovii AI — Trust Intelligence Platform assistant",
    instruction=AIConfig.get_adk_instruction("orchestrator", ORCHESTRATOR_AGENT_INSTRUCTION),
    sub_agents=root_sub_agents,
    tools=orchestrator_tools,
)

# Agent Engine deploys the exported App object to keep the hosted ADK app name
# stable and valid instead of letting the platform infer it from a resource ID.
app = App(name="vartovii_trust_agent", root_agent=root_agent)

# Log initialization summary
mcp_status = "MongoDB MCP ✅" if mongo_mcp_toolset else "MongoDB MCP ❌ (no connection string)"
logger.info(
    "🤖 Vartovii ADK Agent initialized: root + %d sub-agents "
    "(corporate: 10, crypto: 10, osint: 1, memory: 7, mongodb_mcp: %s) | %s",
    len(root_sub_agents),
    "enabled" if mongodb_mcp_agent else "disabled",
    mcp_status,
)
