"""
Routing Adapter Service — Smart Language, RAG, and Tool routing logic.

This service parses inputs, detects language (UA/EN), and routes queries to
either the ADK multi-agent pipeline, standard chat, grounding, or RAG.
It includes resilient fallback paths and state continuation logic.
"""

import logging
import time
from typing import Callable, Dict, List, Optional

from agent.config import AIConfig
from services.telemetry import telemetry

logger = logging.getLogger(__name__)


class ChatRoutingAdapter:
    """Detects request intent (tools, grounding, language) and routes to correct pipeline."""

    FOLLOW_UP_ACKNOWLEDGEMENTS = {
        "yes", "yeah", "yep", "sure", "ok", "okay", "go ahead", "continue", "proceed",
        "так", "ага", "да", "давай", "добре", "ок", "окей", "продовжуй",
    }

    FOLLOW_UP_DETAIL_PHRASES = (
        "more detail", "more details", "tell me more", "go deeper", "continue analysis",
        "what next", "what should i do next", "next step", "next steps",
        "розкажи детальніше", "більш детально", "детальніше", "глибше",
        "продовжуй аналіз", "поясни детальніше", "а далі", "що далі",
    )

    TOOL_HANDOFF_PHRASES = (
        "trust score", "get detailed", "please wait", "let me do that", "let me get",
        "загальний показник довіри", "дозвольте мені це зробити", "дозволь мені це зробити",
        "зачекайте", "отримати", "аналіз", "гаманець", "wallet", "transaction",
        "company", "crypto", "token",
    )

    GROUNDING_KEYWORDS = (
        "latest", "current", "today", "news", "recent", "update", "market", "stock",
        "price", "trend", "happening", "is it true", "verify", "fact check", "confirm",
        "what is", "who is", "tell me about", "information about", "compare to",
        "competitor", "industry", "right now", "this week", "this month",
        "2024", "2025", "2026",
        "останні", "новини", "сьогодні", "ринок", "ціна", "що таке", "хто такий",
        "розкажи про", "порівняй",
    )

    TOOL_KEYWORDS = (
        "company", "companies", "employer", "employers", "компан", "роботодав", "фірм",
        "trust score", "trust-score", "trustscore", "траст скор", "оцінк", "рейтинг",
        "bmw", "audi", "lidl", "sap", "bosch", "siemens", "amazon", "mercedes",
        "spotify", "netflix", "google", "microsoft", "apple",
        "crypto", "token", "coin", "protocol", "blockchain", "chain", "defi",
        "bitcoin", "btc", "ethereum", "eth", "solana", "monad", "enso", "aster",
        "крипто", "токен", "коін", "монета", "блокчейн",
        "find", "search", "look up", "check", "знайди", "знайти", "пошук", "перевір",
        "top", "best", "worst", "ranking", "list", "топ", "найкращ", "найгірш", "список",
        "analyze", "analysis", "review", "reviews", "аналіз", "відгук", "відгуки",
        "compare", "comparison", "versus", "vs", "порівняй", "порівняння", "проти",
        "start analysis", "run analysis", "collect data", "проаналізуй", "запусти аналіз",
        "show reviews", "employee feedback", "покажи відгуки", "що кажуть",
        "wallet", "address", "0x", "balance", "transaction", "transactions",
        "holder", "holders", "contract", "on-chain", "onchain", "forensic",
        "гаманець", "адреса", "баланс", "транзакц", "холдер",
    )

    UKRAINIAN_CHARS = set("їієґЇІЄҐ")
    UKRAINIAN_WORDS = (
        "що", "як", "це", "та", "але", "або", "для", "про", "від", "до", "яка",
        "який", "яке", "які", "чому", "коли", "де", "хто", "допоможи", "покажи",
        "розкажи", "поясни", "знайди", "проаналізуй",
    )

    def __init__(
        self,
        *,
        get_capabilities: Callable[[], Dict],
        chat_with_adk: Callable[..., Dict],
        chat_with_tools: Callable[..., Dict],
        chat_with_rag: Callable[..., Dict],
        chat_with_grounding: Callable[..., Dict],
        chat_standard: Callable[..., Dict],
    ):
        self.get_capabilities = get_capabilities
        self.chat_with_adk = chat_with_adk
        self.chat_with_tools = chat_with_tools
        self.chat_with_rag = chat_with_rag
        self.chat_with_grounding = chat_with_grounding
        self.chat_standard = chat_standard

    def chat(
        self,
        *,
        message: str,
        history: Optional[List[Dict]] = None,
        company_context: Optional[str] = None,
        conversation_id: Optional[str] = None,
        language: str = "auto",
        enable_grounding: Optional[bool] = None,
        enable_rag: Optional[bool] = None,
        enable_tools: Optional[bool] = None,
        attachments: Optional[List[Dict]] = None,
    ) -> Dict:
        """Process chat message, route through the correct handler, and track telemetry."""
        start_time = time.time()
        resolved_language = self._resolve_language(language=language, message=message, history=history)
        capabilities = self.get_capabilities()

        # Telemetry record for routing decision
        telemetry.record_invocation("routing_adapter")

        try:
            # 1. Check Tool Calling / ADK Agent path
            use_tools = self._resolve_tools_usage(
                message=message,
                history=history,
                enable_tools=enable_tools,
                function_calling_enabled=capabilities.get("function_calling_enabled", False),
            )
            
            if use_tools and capabilities.get("function_calling_enabled", False):
                if capabilities.get("adk_enabled") and capabilities.get("adk_runner"):
                    try:
                        telemetry.record_invocation("adk_orchestrator")
                        response = self.chat_with_adk(
                            message,
                            history,
                            company_context,
                            resolved_language,
                            conversation_id=conversation_id,
                        )
                        # Record tool frequency
                        for tool in response.get("adk_tools", []):
                            telemetry.record_tool_call(tool)
                        return response
                    except Exception as error:
                        logger.warning("⚠️ ADK agent failed, falling back to legacy tools: %s", error)
                        telemetry.record_fallback("agent", "adk", "legacy_tools")
                
                telemetry.record_invocation("legacy_tools")
                return self.chat_with_tools(message, history, company_context, resolved_language)

            # 2. Check RAG path
            use_rag = self._resolve_rag_usage(
                message=message,
                enable_rag=enable_rag,
                rag_enabled=capabilities.get("rag_enabled", False),
                retrieval_service=capabilities.get("retrieval_service"),
            )
            if use_rag and capabilities.get("rag_enabled", False):
                telemetry.record_invocation("rag")
                return self.chat_with_rag(message, history, company_context, resolved_language)

            # 3. Check Google Search Grounding path
            use_grounding = self._resolve_grounding_usage(
                message=message,
                enable_grounding=enable_grounding,
            )
            if use_grounding and capabilities.get("grounding_enabled", False):
                telemetry.record_invocation("grounding")
                return self.chat_with_grounding(message, history, company_context, resolved_language)

            # 4. Fallback to standard chat
            telemetry.record_invocation("standard_chat")
            return self.chat_standard(message, history, company_context, resolved_language, attachments)

        finally:
            duration = time.time() - start_time
            telemetry.record_latency(duration)

    @classmethod
    def _resolve_language(cls, *, language: str, message: str, history: Optional[List[Dict]] = None) -> str:
        """Detect language if auto-detect is set."""
        if language != "auto":
            return language
        detected = cls._detect_language(message)
        if detected != "en":
            return detected

        if history:
            for msg in reversed(history[-4:]):
                text = str(msg.get("text", "")).strip()
                if not text:
                    continue
                historical_language = cls._detect_language(text)
                if historical_language != "en":
                    return historical_language

        return detected

    @classmethod
    def _resolve_tools_usage(
        cls,
        *,
        message: str,
        history: Optional[List[Dict]],
        enable_tools: Optional[bool],
        function_calling_enabled: bool,
    ) -> Optional[bool]:
        """Determine if tool/agent system should process this query."""
        use_tools = enable_tools
        if use_tools is None and function_calling_enabled:
            use_tools = cls._should_use_tools(message) or cls._should_continue_tool_context(message, history)
        return use_tools

    @classmethod
    def _resolve_rag_usage(
        cls,
        *,
        message: str,
        enable_rag: Optional[bool],
        rag_enabled: bool,
        retrieval_service,
    ) -> Optional[bool]:
        """Determine if RAG retrieval is required."""
        use_rag = enable_rag
        if use_rag is None and rag_enabled and retrieval_service:
            use_rag = retrieval_service.should_use_rag(message)
        return use_rag

    @classmethod
    def _resolve_grounding_usage(
        cls,
        *,
        message: str,
        enable_grounding: Optional[bool],
    ) -> Optional[bool]:
        """Determine if live web search grounding is required."""
        use_grounding = enable_grounding
        if use_grounding is None:
            use_grounding = cls._should_use_grounding(message)
        return use_grounding

    @classmethod
    def _should_use_grounding(cls, message: str) -> bool:
        """Detect grounding terms in user query."""
        lowered = message.lower()
        return any(keyword in lowered for keyword in cls.GROUNDING_KEYWORDS)

    @classmethod
    def _should_use_tools(cls, message: str) -> bool:
        """Detect tool terms in user query."""
        lowered = message.lower()
        return any(keyword in lowered for keyword in cls.TOOL_KEYWORDS)

    @classmethod
    def _should_continue_tool_context(cls, message: str, history: Optional[List[Dict]]) -> bool:
        """Keep tool context active for conversational follow-ups."""
        if not history:
            return False

        lowered = message.lower().strip()
        if not lowered:
            return False

        is_ack = lowered in cls.FOLLOW_UP_ACKNOWLEDGEMENTS
        is_detail_request = any(phrase in lowered for phrase in cls.FOLLOW_UP_DETAIL_PHRASES)
        if not is_ack and not is_detail_request:
            return False

        recent_history = " ".join(str(msg.get("text", "")) for msg in history[-4:]).lower()
        if not recent_history.strip():
            return False

        return cls._should_use_tools(recent_history) or any(
            phrase in recent_history for phrase in cls.TOOL_HANDOFF_PHRASES
        )

    @classmethod
    def _detect_language(cls, message: str) -> str:
        """Detect Ukrainian vs English based on characters and common keywords."""
        if any(char in message for char in cls.UKRAINIAN_CHARS):
            return "ua"

        lowered = message.lower()
        ukrainian_word_count = sum(1 for word in cls.UKRAINIAN_WORDS if word in lowered)
        if ukrainian_word_count >= 2:
            return "ua"

        return "en"
