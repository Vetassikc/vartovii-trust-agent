"""
Tests for Vartovii Trust Agent services (Routing, Model Runtime, Telemetry).
"""

import pytest
from services.telemetry import AgentTelemetry
from services.model_runtime import ChatModelRuntime
from services.routing_adapter import ChatRoutingAdapter
from agent.config import AIConfig


class TestTelemetryService:
    """Verify telemetry collection works correctly."""

    def test_record_invocation(self):
        t = AgentTelemetry()
        t.record_invocation("test_agent")
        assert t.metrics["invocations"] == 1
        assert t.metrics["agent_usage"]["test_agent"] == 1

    def test_record_latency_and_sla(self):
        t = AgentTelemetry()
        t.record_latency(5.0)
        assert t.metrics["latency_records"] == [5.0]
        assert t.metrics["sla_breaches"] == 0

        # Record breach
        t.record_latency(20.0)
        assert t.metrics["sla_breaches"] == 1

    def test_record_fallback(self):
        t = AgentTelemetry()
        t.record_fallback("chat", "gemini-3.1-pro-preview", "gemini-3.5-flash")
        assert t.metrics["fallback_activations"] == 1

    def test_get_summary(self):
        t = AgentTelemetry()
        t.record_invocation("crypto_agent")
        t.record_latency(2.5)
        t.record_tool_call("check_wallet")
        t.record_session(reused=True)
        t.record_session(reused=False)

        summary = t.get_summary()
        assert summary["total_runs"] == 1
        assert summary["average_latency"] == 2.5
        assert summary["session_reuse_ratio"] == 0.5
        assert "check_wallet" in summary["popular_tools"]


class TestModelRuntimeService:
    """Verify model runtime fallback chains and generation mocks."""

    def test_generate_text_fallback_success(self):
        runtime = ChatModelRuntime()
        # Should execute successfully via fallback to mock
        response = runtime.generate_text("Hello", system_instruction="Be polite")
        assert "Mock response from" in response
        assert "Trust assessment" in response

    def test_generate_with_grounding_sources(self):
        runtime = ChatModelRuntime()
        response = runtime.generate_with_grounding("Check current bitcoin status", system_instruction="Use search")
        sources = runtime.extract_grounding_sources(response)
        assert len(sources) > 0
        assert sources[0]["type"] == "google_search"


class TestRoutingAdapterService:
    """Verify chat routing logic, language detection, and context continuation."""

    def test_language_detection_english(self):
        lang = ChatRoutingAdapter._detect_language("Show me the trust score for SAP")
        assert lang == "en"

    def test_language_detection_ukrainian(self):
        # Specific Ukrainian characters
        lang = ChatRoutingAdapter._detect_language("Привіт, покажи інформацію про компанію")
        assert lang == "ua"

    def test_language_detection_ukrainian_words(self):
        # Ukrainian common words count
        lang = ChatRoutingAdapter._detect_language("яка компанія це робить")
        assert lang == "ua"

    def test_should_use_tools(self):
        assert ChatRoutingAdapter._should_use_tools("Check trust score of BMW") is True
        assert ChatRoutingAdapter._should_use_tools("Check wallet balance of 0x0") is True
        assert ChatRoutingAdapter._should_use_tools("Hello chatbot") is False

    def test_should_use_grounding(self):
        assert ChatRoutingAdapter._should_use_grounding("What are the latest updates today?") is True
        assert ChatRoutingAdapter._should_use_grounding("Hello chatbot") is False

    def test_should_continue_tool_context(self):
        history = [
            {"role": "user", "text": "Check trust score of BMW"},
            {"role": "assistant", "text": "The trust score of BMW is 82."}
        ]
        # Follow-up "continue" or "more details"
        assert ChatRoutingAdapter._should_continue_tool_context("tell me more", history) is True
        assert ChatRoutingAdapter._should_continue_tool_context("go deeper", history) is True
        assert ChatRoutingAdapter._should_continue_tool_context("hello", history) is False

    def test_routing_chat_standard(self):
        # Setup routing with mock handlers
        called = {}

        def mock_caps():
            return {"function_calling_enabled": True, "adk_enabled": False}

        def mock_chat_standard(*args, **kwargs):
            called["standard"] = True
            return {"response": "standard_res"}

        routing = ChatRoutingAdapter(
            get_capabilities=mock_caps,
            chat_with_adk=lambda *args, **kwargs: {},
            chat_with_tools=lambda *args, **kwargs: {},
            chat_with_rag=lambda *args, **kwargs: {},
            chat_with_grounding=lambda *args, **kwargs: {},
            chat_standard=mock_chat_standard,
        )

        res = routing.chat(message="Just a standard query")
        assert res["response"] == "standard_res"
        assert called.get("standard") is True
