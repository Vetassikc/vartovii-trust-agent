"""Tests for dashboard API fallback behavior."""

import pytest

from api import dashboard_api


@pytest.fixture(autouse=True)
def reset_mongodb_state(monkeypatch):
    """Keep dashboard tests on the no-secret mock path."""
    monkeypatch.setattr(dashboard_api, "_db", None)
    monkeypatch.setattr(dashboard_api, "_mongo_client", None)


@pytest.mark.asyncio
async def test_stats_falls_back_to_mock_data_without_mongodb():
    result = await dashboard_api.get_stats()

    assert result["source"] == "mock"
    assert result["total_companies"] > 0
    assert result["total_crypto_projects"] > 0
    assert result["avg_trust_score"] > 0


@pytest.mark.asyncio
async def test_leaderboard_falls_back_to_mock_companies_without_mongodb():
    result = await dashboard_api.get_leaderboard(type="companies", limit=2)

    assert result["source"] == "mock"
    assert result["count"] == 2
    assert result["leaderboard"][0]["trust_score"] >= result["leaderboard"][1]["trust_score"]
    assert "profile_slug" in result["leaderboard"][0]


@pytest.mark.asyncio
async def test_entity_detail_uses_wrapped_entity_contract_without_mongodb():
    result = await dashboard_api.get_entity_detail("company", "sap-se")

    assert result["source"] == "mock"
    assert result["entity_type"] == "company"
    assert result["entity"]["company_name"] == "SAP"
    assert result["entity"]["reviews"]


@pytest.mark.asyncio
async def test_investigations_fallback_returns_demo_evidence():
    result = await dashboard_api.get_investigations(limit=5)

    assert result["source"] == "mock"
    assert result["count"] > 0
    assert result["investigations"][0]["entity_name"] == "Wirecard AG"
    assert result["investigations"][0]["risk_level"] == "CRITICAL"


@pytest.mark.asyncio
async def test_audit_fallback_returns_demo_events():
    result = await dashboard_api.get_audit_trail(limit=5)

    assert result["source"] == "mock"
    assert result["count"] > 0
    assert result["events"][0]["agent"] == "vartovii_orchestrator"


def test_public_audit_model_metadata_uses_active_policy():
    assert dashboard_api._public_model_used("gemini-1.5-pro") == dashboard_api.AIConfig.ADK_MODEL
    assert dashboard_api._public_model_used("mongodb-mcp-server") == "mongodb-mcp-server"


@pytest.mark.asyncio
async def test_health_check_exposes_model_metadata_without_secrets():
    result = await dashboard_api.health_check()

    assert result["agent_runtime"] == "google_adk"
    assert result["model_profile"] in {"stable", "cost", "preview"}
    assert result["agent_model"].startswith("gemini-")
    assert result["chat_model"].startswith("gemini-")


@pytest.mark.asyncio
async def test_readiness_check_exposes_hackathon_evidence_without_secrets():
    result = await dashboard_api.readiness_check()

    assert result["status"] == "ready"
    assert result["submission"]["hosted_url"].startswith("https://")
    assert result["submission"]["demo_video"] == "pending"
    assert result["agent_engine"]["status"] in {"deployed", "deployable"}
    assert "reasoningEngines" in result["agent_engine"]["resource"]
    assert result["quality"]["test_count"] == 63
    assert {item["name"] for item in result["requirements"]} == {
        "Gemini-powered AI agent",
        "Google Cloud Agent Builder path",
        "Partner MCP server",
        "Hosted production service",
        "Live evidence proof",
        "Live wallet proof",
    }
    assert result["quality"]["live_sources"] == ["CoinGecko", "Etherscan"]


@pytest.mark.asyncio
async def test_judge_trace_fallback_exposes_single_proof_bundle():
    result = await dashboard_api.judge_trace()

    assert result["source"] == "mock"
    assert result["scenario"]["track"] == "MongoDB"
    assert result["decision"]["entity_name"] == "Wirecard AG"
    assert result["runtime"]["agent_model"].startswith("gemini-")
    assert result["mcp_proof"]["server"] == "mongodb-mcp-server"
    assert [step["step"] for step in result["trace"]] == [1, 2, 3, 4, 5]
    assert result["audit_events"]


@pytest.mark.asyncio
async def test_live_proof_fetches_coingecko_evidence_without_secrets(monkeypatch):
    def fake_fetch(slug):
        return {
            "available": True,
            "provider": "coingecko",
            "coingecko_id": slug,
            "requested_slug": slug,
            "fetched_at": "2026-06-05T10:00:00+00:00",
            "source_url": "https://api.coingecko.com/api/v3/simple/price?ids=ethereum",
            "price_usd": 3900.25,
            "market_cap_usd": 470000000000,
            "volume_24h_usd": 21000000000,
            "price_change_24h_pct": -11.2,
        }

    monkeypatch.setattr(dashboard_api, "fetch_coingecko_market_data", fake_fetch)

    result = await dashboard_api.live_proof(slug="ethereum", force=True)

    assert result["status"] == "ready"
    assert result["live_api_called"] is True
    assert result["target"]["slug"] == "ethereum"
    assert result["live_evidence"]["base_trust_score"] == 94
    assert result["live_evidence"]["live_trust_delta"] == -4
    assert result["live_evidence"]["live_adjusted_trust_score"] == 90
    assert result["mongodb_proof"]["status"] == "skipped_no_mongodb"
    assert [step["step"] for step in result["agent_trace"]] == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_wallet_live_proof_fetches_etherscan_balance_without_secrets(monkeypatch):
    def fake_fetch(address, api_key):
        assert address == "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        assert api_key == "test-etherscan-key"
        return {
            "available": True,
            "provider": "etherscan",
            "chain_id": "1",
            "address": address,
            "fetched_at": "2026-06-05T10:00:00+00:00",
            "source_url": (
                "https://api.etherscan.io/v2/api?"
                "chainid=1&module=account&action=balance&address="
                "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045&tag=latest"
            ),
            "balance_wei": "1234500000000000000",
            "eth_balance": 1.2345,
            "eth_balance_display": "1.2345",
        }

    monkeypatch.setattr(dashboard_api, "ETHERSCAN_API_KEY", "test-etherscan-key")
    monkeypatch.setattr(dashboard_api, "fetch_etherscan_wallet_balance", fake_fetch)

    result = await dashboard_api.wallet_live_proof(
        address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        force=True,
    )

    assert result["status"] == "ready"
    assert result["live_api_called"] is True
    assert result["target"]["entity_type"] == "wallet"
    assert result["source_freshness"]["provider"] == "Etherscan"
    assert result["wallet_evidence"]["eth_balance"] == 1.2345
    assert result["mongodb_proof"]["status"] == "skipped_no_mongodb"
    assert [step["step"] for step in result["agent_trace"]] == [1, 2, 3, 4, 5]
    assert "test-etherscan-key" not in str(result)


@pytest.mark.asyncio
async def test_wallet_live_proof_degrades_without_etherscan_key(monkeypatch):
    monkeypatch.setattr(dashboard_api, "ETHERSCAN_API_KEY", "")

    result = await dashboard_api.wallet_live_proof(
        address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        force=True,
    )

    assert result["status"] == "degraded"
    assert result["source"] == "wallet_fallback"
    assert result["live_api_called"] is False
    assert result["wallet_evidence"]["balance"]["error"] == "missing_api_key"
    assert result["wallet_evidence"]["eth_balance"] == 1247.83
    assert result["mongodb_proof"]["status"] == "not_persisted_no_live_balance"
    assert result["agent_trace"][1]["evidence"] == "missing_api_key"
