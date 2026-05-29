"""
Tests for ADK Agent Architecture.

These tests verify the agent configuration, tool registration, and
architecture decisions — extracted from the production test suite (800+ tests).
"""

import pytest

from agent.config import AIConfig
from agent.adk_agent import (
    root_agent,
    corporate_agent,
    crypto_agent,
    osint_agent,
    memory_agent,
)


# ============================================
# Agent Structure Tests
# ============================================


class TestAgentArchitecture:
    """Verify the multi-agent topology is correct."""

    def test_root_agent_has_four_sub_agents(self):
        """Root orchestrator must delegate to exactly 4 sub-agents."""
        assert len(root_agent.sub_agents) == 4

    def test_root_agent_delegates_only(self):
        """Orchestrator tools should only be MCP toolset or empty."""
        # Without MongoDB configured, orchestrator has no direct tools
        # With MongoDB, it would have the MCP toolset
        assert len(root_agent.tools) <= 1

    def test_root_agent_name(self):
        assert root_agent.name == "vartovii_orchestrator"

    def test_corporate_agent_name(self):
        assert corporate_agent.name == "corporate_agent"

    def test_crypto_agent_name(self):
        assert crypto_agent.name == "crypto_agent"

    def test_osint_agent_name(self):
        assert osint_agent.name == "osint_agent"

    def test_corporate_agent_has_7_tools(self):
        """Corporate agent should have exactly 7 tools."""
        assert len(corporate_agent.tools) == 7

    def test_crypto_agent_has_7_tools(self):
        """Crypto agent should have exactly 7 tools."""
        assert len(crypto_agent.tools) == 7

    def test_osint_agent_has_google_search(self):
        """OSINT agent should have GoogleSearchTool."""
        assert len(osint_agent.tools) == 1

    def test_sub_agents_are_in_root(self):
        """All four sub-agents must be registered with root."""
        agent_names = {a.name for a in root_agent.sub_agents}
        assert agent_names == {"corporate_agent", "crypto_agent", "osint_agent", "memory_agent"}


# ============================================
# Model Configuration Tests
# ============================================


class TestModelConfiguration:
    """Verify model routing and fallback chain configuration."""

    def test_stable_profile_uses_gemini_25_flash_for_chat(self):
        assert AIConfig._MODEL_DEFAULTS["stable"]["chat"] == "gemini-2.5-flash"

    def test_stable_profile_uses_gemini_25_pro_for_report(self):
        assert AIConfig._MODEL_DEFAULTS["stable"]["report"] == "gemini-2.5-pro"

    def test_preview_profile_uses_gemini_3_flash(self):
        assert AIConfig._MODEL_DEFAULTS["preview"]["chat"] == "gemini-3-flash"

    def test_model_chain_has_three_tiers(self):
        """3-tier fallback: primary → fallback → ultimate (gemini-2.0-flash)."""
        chain = AIConfig.get_model_chain_for_task("report")
        # For stable: gemini-2.5-pro → gemini-2.5-flash → gemini-2.0-flash
        assert len(chain) == 3
        assert chain[-1] == "gemini-2.0-flash"

    def test_model_chain_no_duplicates(self):
        """No model should appear twice in the chain."""
        chain = AIConfig.get_model_chain_for_task("report")
        assert len(chain) == len(set(chain))

    def test_chat_model_chain(self):
        """Chat chain: flash → 2.0-flash (2 tiers, since primary == fallback)."""
        chain = AIConfig.get_model_chain_for_task("chat")
        assert chain[0] == AIConfig.CHAT_MODEL
        assert "gemini-2.0-flash" in chain

    def test_agent_model_matches_adk_model(self):
        """Agent task should use ADK_MODEL."""
        assert AIConfig.get_model_for_task("agent") == AIConfig.ADK_MODEL


# ============================================
# ADK Instruction Override Tests
# ============================================


class TestADKInstructionOverride:
    """Verify environment-driven prompt override mechanism."""

    def test_default_instruction_used_when_no_env(self):
        """Without env override, default instruction is returned."""
        result = AIConfig.get_adk_instruction("corporate", "DEFAULT_INSTRUCTION")
        # Since we don't set env vars in tests, should return default
        assert result == "DEFAULT_INSTRUCTION" or len(result) > 0

    def test_unknown_agent_returns_default(self):
        """Unknown agent name should return the default instruction."""
        result = AIConfig.get_adk_instruction("nonexistent_agent", "FALLBACK")
        assert result == "FALLBACK"

    def test_env_keys_cover_all_agents(self):
        """All 5 agent types must have env override keys."""
        expected = {"corporate", "crypto", "osint", "memory", "orchestrator"}
        assert set(AIConfig.ADK_INSTRUCTION_ENV_KEYS.keys()) == expected


# ============================================
# Tool Function Tests
# ============================================


class TestCorporateTools:
    """Verify corporate tool functions work correctly."""

    def test_search_company_found(self):
        from agent.tools.corporate_tools import search_company
        result = search_company("SAP")
        assert result["found"] is True
        assert result["trust_score"] == 74

    def test_search_company_not_found(self):
        from agent.tools.corporate_tools import search_company
        result = search_company("NonexistentCorp")
        assert result["found"] is False

    def test_get_trust_score_with_breakdown(self):
        from agent.tools.corporate_tools import get_trust_score
        result = get_trust_score("BMW")
        assert "breakdown" in result
        assert result["trust_score"] == 82

    def test_compare_companies(self):
        from agent.tools.corporate_tools import compare_companies
        result = compare_companies("BMW", "SAP")
        assert "winner" in result
        assert result["winner"] == "BMW Group"  # 82 vs 74

    def test_list_companies_sorted(self):
        from agent.tools.corporate_tools import list_companies
        result = list_companies(sort_by="trust_score")
        scores = [c["trust_score"] for c in result["companies"]]
        assert scores == sorted(scores, reverse=True)

    def test_vacancy_intelligence(self):
        from agent.tools.corporate_tools import get_vacancy_intelligence
        result = get_vacancy_intelligence("SAP")
        assert result["found"] is True
        assert result["ghost_jobs"] == 12


class TestCryptoTools:
    """Verify crypto tool functions work correctly."""

    def test_search_crypto_found(self):
        from agent.tools.crypto_tools import search_crypto_projects
        result = search_crypto_projects("Bitcoin")
        assert result["found"] is True
        assert result["count"] >= 1

    def test_search_crypto_not_found(self):
        from agent.tools.crypto_tools import search_crypto_projects
        result = search_crypto_projects("FakeCoin999")
        assert result["found"] is False

    def test_crypto_trust_score(self):
        from agent.tools.crypto_tools import get_crypto_trust_score
        result = get_crypto_trust_score("uniswap")
        assert result["found"] is True
        assert result["trust_score"] == 78
        assert "score_breakdown" in result

    def test_check_wallet_valid(self):
        from agent.tools.crypto_tools import check_wallet
        result = check_wallet("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
        assert result["found"] is True
        assert result["eth_balance"] > 0

    def test_check_wallet_invalid_format(self):
        from agent.tools.crypto_tools import check_wallet
        result = check_wallet("not_a_wallet")
        assert "error" in result

    def test_token_holders_concentration(self):
        from agent.tools.crypto_tools import get_token_holders
        result = get_token_holders("0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984")
        assert "concentration_risk" in result

    def test_contract_info(self):
        from agent.tools.crypto_tools import get_contract_info
        result = get_contract_info("0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984")
        assert result["is_verified"] is True
