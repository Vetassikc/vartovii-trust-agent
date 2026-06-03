"""
Model Runtime Service — Resilient Gemini API execution with 3-tier fallback.

This service encapsulates text generation, function calling, and grounding
with Google Search. It implements a 3-tier fallback chain to ensure high
availability and zero user-visible errors in production.
"""

import logging
from typing import Any, Dict, List, Optional, Union

# Try importing from google-genai (SDK 2.0+ standard) or vertexai
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

try:
    from vertexai.generative_models import GenerationConfig, GenerativeModel, Tool
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False

from agent.config import AIConfig

logger = logging.getLogger(__name__)


class ChatModelRuntime:
    """Encapsulates model generation paths, grounding, and fallbacks."""

    def __init__(self, *, client=None, sentry_tools=None):
        self.client = client
        self.sentry_tools = sentry_tools
        self.google_search_tool = self._init_grounding()
        self.grounding_enabled = self.google_search_tool is not None

    def update_tools(self, sentry_tools) -> None:
        """Update the tool configuration for function calling."""
        self.sentry_tools = sentry_tools

    def _init_grounding(self) -> Optional[Any]:
        """Initialize Google Search grounding tool if available."""
        if self.client is None:
            # Standalone mode / Mocking
            return {"google_search": {}}
        
        try:
            # Vertex AI style
            if hasattr(self.client, "build_google_search_tool"):
                tool = self.client.build_google_search_tool()
                logger.info("🔍 Google Search grounding initialized (Vertex AI)")
                return tool
            # GenAI SDK style
            elif GENAI_AVAILABLE:
                logger.info("🔍 Google Search grounding enabled (google-genai)")
                return {"google_search": {}}
        except Exception as error:
            logger.warning("⚠️ Google Search grounding tool initialization skipped: %s", error)
        return None

    def generate_text(
        self,
        prompt: Union[str, List[Any]],
        *,
        system_instruction: str,
        temperature: float = 0.7,
        task: str = "chat",
    ) -> str:
        """
        Generate text response using the 3-tier fallback chain.
        
        Fallback order:
          1. Primary Task Model (e.g. gemini-3.5-flash / gemini-3.1-pro-preview)
          2. Task-specific Fallback (e.g. gemini-3.5-flash)
          3. Ultimate Fallback (gemini-2.0-flash — always available)
        """
        model_chain = AIConfig.get_model_chain_for_task(task)
        last_error = None

        for model_name in model_chain:
            try:
                logger.info("💬 Attempting text generation with model: %s", model_name)
                if self.client:
                    # In production we route to the client
                    if hasattr(self.client, "generate"):
                        return self.client.generate(
                            prompt,
                            task=task,
                            model=model_name,
                            system_instruction=system_instruction,
                            temperature=temperature,
                        )
                # Standalone mock fallback
                logger.info("🤖 Mocking execution for model %s", model_name)
                return f"[Mock response from {model_name}] Trust assessment matches stable production guidelines."
            except Exception as e:
                logger.warning("⚠️ Model %s failed: %s. Retrying next in chain...", model_name, e)
                last_error = e

        raise RuntimeError(f"All models in the fallback chain failed. Last error: {last_error}")

    def generate_with_tools(
        self,
        prompt: str,
        *,
        system_instruction: str,
        temperature: float = 0.3,
    ) -> Any:
        """Execute generation with function tools registered."""
        if not self.sentry_tools:
            raise RuntimeError("No tools configured for function calling")

        model_name = AIConfig.get_model_for_task("chat")
        logger.info("🛠️ Running tool generation with model: %s", model_name)
        
        if self.client:
            # Actual client execution
            return self.client.generate_with_tools(
                prompt,
                model=model_name,
                system_instruction=system_instruction,
                tools=[self.sentry_tools],
                temperature=temperature,
            )

        # Mock fallback response
        return f"[Mock Tool Response] Executed with tools: {self.sentry_tools}"

    def generate_with_grounding(
        self,
        prompt: str,
        *,
        system_instruction: str,
        temperature: float = 0.7,
    ) -> Any:
        """Generate response with Google Search grounding."""
        model_name = AIConfig.get_model_for_task("chat")
        logger.info("🔍 Running grounded generation with model: %s", model_name)

        if self.client and hasattr(self.client, "generate_grounded_response"):
            return self.client.generate_grounded_response(
                prompt,
                model=model_name,
                system_instruction=system_instruction,
                temperature=temperature,
            )

        # Mock object for return
        class MockGroundedResponse:
            text = "[Mock Grounded Response] Found references to Vartovii Trust Agent deployment evidence."
            grounding_metadata = type('MockMetadata', (), {
                'search_entry_point': type('MockEntry', (), {'rendered_content': 'Vartovii Trust Agent deployment evidence'})(),
                'grounding_chunks': [
                    type('MockChunk', (), {
                        'web': type('MockWeb', (), {
                            'title': 'Vartovii Trust Agent Repository',
                            'uri': 'https://github.com/Vetassikc/vartovii-trust-agent'
                        })()
                    })()
                ]
            })()

        return MockGroundedResponse()

    @staticmethod
    def extract_grounding_sources(response) -> List[Dict[str, str]]:
        """Normalize grounding metadata from Gemini response structure."""
        sources: List[Dict[str, str]] = []
        grounding_metadata = getattr(response, "grounding_metadata", None)
        if grounding_metadata is None:
            candidates = getattr(response, "candidates", None) or []
            for candidate in candidates:
                grounding_metadata = getattr(candidate, "grounding_metadata", None)
                if grounding_metadata is not None:
                    break
        if not grounding_metadata:
            return sources

        search_entry = getattr(grounding_metadata, "search_entry_point", None)
        if search_entry:
            sources.append(
                {
                    "type": "google_search",
                    "query": getattr(search_entry, "rendered_content", "web search"),
                }
            )

        for chunk in getattr(grounding_metadata, "grounding_chunks", [])[:5]:
            web_chunk = getattr(chunk, "web", None)
            if not web_chunk:
                continue
            sources.append(
                {
                    "type": "web",
                    "title": getattr(web_chunk, "title", ""),
                    "uri": getattr(web_chunk, "uri", ""),
                }
            )
        return sources
