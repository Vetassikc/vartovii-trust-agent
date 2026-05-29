"""
Vartovii Trust Intelligence Agent — Configuration

Central configuration for AI models, fallback chains, and agent behavior.
All settings are environment-overridable for production flexibility.
"""

import os


def _get_bool_env(name: str, default: bool) -> bool:
    """Read boolean env vars in a predictable way."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class AIConfig:
    """Central configuration for AI services and agent models."""

    # ============================================
    # Model Profiles: stable (GA) vs preview (3.x)
    # ============================================
    MODEL_PROFILE = os.getenv("GEMINI_MODEL_PROFILE", "preview").strip().lower()
    if MODEL_PROFILE not in {"stable", "preview"}:
        MODEL_PROFILE = "preview"

    _MODEL_DEFAULTS = {
        "stable": {
            "chat": "gemini-2.5-flash",
            "report": "gemini-2.5-pro",
            "sentiment": "gemini-2.5-flash",
            "agent": "gemini-2.5-flash",
        },
        "preview": {
            "chat": "gemini-3-flash",
            "report": "gemini-3-pro",
            "sentiment": "gemini-3-flash",
            "agent": "gemini-3-flash",
        },
    }

    # Primary models (env-overridable)
    CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", _MODEL_DEFAULTS[MODEL_PROFILE]["chat"])
    REPORT_MODEL = os.getenv("GEMINI_REPORT_MODEL", _MODEL_DEFAULTS[MODEL_PROFILE]["report"])
    SENTIMENT_MODEL = os.getenv("GEMINI_SENTIMENT_MODEL", _MODEL_DEFAULTS[MODEL_PROFILE]["sentiment"])
    ADK_MODEL = os.getenv("GEMINI_ADK_MODEL", _MODEL_DEFAULTS[MODEL_PROFILE]["agent"])

    # ============================================
    # 3-Tier Fallback Chain
    # ============================================
    MODEL_FALLBACK_ENABLED = _get_bool_env("GEMINI_MODEL_FALLBACK_ENABLED", True)
    CHAT_FALLBACK_MODEL = os.getenv("GEMINI_CHAT_FALLBACK_MODEL", _MODEL_DEFAULTS["stable"]["chat"])
    REPORT_FALLBACK_MODEL = os.getenv("GEMINI_REPORT_FALLBACK_MODEL", _MODEL_DEFAULTS["stable"]["chat"])
    SENTIMENT_FALLBACK_MODEL = os.getenv("GEMINI_SENTIMENT_FALLBACK_MODEL", _MODEL_DEFAULTS["stable"]["sentiment"])
    ADK_FALLBACK_MODEL = os.getenv("GEMINI_ADK_FALLBACK_MODEL", _MODEL_DEFAULTS["stable"]["agent"])

    # ============================================
    # ADK Agent Configuration
    # ============================================
    ADK_ENABLED = _get_bool_env("ADK_ENABLED", True)

    # Environment-overridable agent instructions (update prompts without code changes)
    ADK_INSTRUCTION_ENV_KEYS = {
        "corporate": "ADK_CORPORATE_INSTRUCTION",
        "crypto": "ADK_CRYPTO_INSTRUCTION",
        "osint": "ADK_OSINT_INSTRUCTION",
        "memory": "ADK_MEMORY_INSTRUCTION",
        "orchestrator": "ADK_ORCHESTRATOR_INSTRUCTION",
    }

    # ============================================
    # MongoDB Configuration
    # ============================================
    MONGODB_ENABLED = _get_bool_env("MONGODB_ENABLED", True)
    MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING", "")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "vartovii")

    # ============================================
    # Generation Defaults
    # ============================================
    DEFAULT_TEMPERATURE = 0.3
    DEFAULT_MAX_TOKENS = 8192
    CHAT_MAX_TOKENS = 8192
    REPORT_MAX_TOKENS = 16384

    @classmethod
    def get_model_for_task(cls, task: str) -> str:
        """Get the appropriate model for a specific task."""
        models = {
            "chat": cls.CHAT_MODEL,
            "report": cls.REPORT_MODEL,
            "sentiment": cls.SENTIMENT_MODEL,
            "agent": cls.ADK_MODEL,
        }
        return models.get(task, cls.CHAT_MODEL)

    @classmethod
    def get_fallback_model_for_task(cls, task: str) -> str:
        """Get fallback model for a specific task."""
        fallbacks = {
            "chat": cls.CHAT_FALLBACK_MODEL,
            "report": cls.REPORT_FALLBACK_MODEL,
            "sentiment": cls.SENTIMENT_FALLBACK_MODEL,
            "agent": cls.ADK_FALLBACK_MODEL,
        }
        return fallbacks.get(task, cls.CHAT_FALLBACK_MODEL)

    @classmethod
    def get_model_chain_for_task(cls, task: str) -> list[str]:
        """
        Return primary→fallback→ultimate chain for resilient generation.

        Three-tier fallback ensures zero user-visible failures:
          1. Primary model (e.g., gemini-2.5-flash)
          2. Task-specific fallback (e.g., gemini-2.5-flash for reports)
          3. Ultimate fallback (gemini-2.0-flash — always available)
        """
        primary = cls.get_model_for_task(task)
        fallback = cls.get_fallback_model_for_task(task)
        chain = [primary]
        if cls.MODEL_FALLBACK_ENABLED and fallback and fallback != primary:
            chain.append(fallback)

        ultimate_fallback = "gemini-2.0-flash"
        if cls.MODEL_FALLBACK_ENABLED and ultimate_fallback not in chain:
            chain.append(ultimate_fallback)

        return chain

    @classmethod
    def get_adk_instruction(cls, agent_name: str, default: str) -> str:
        """
        Resolve ADK instruction text from environment with safe default.

        This allows prompt updates without code changes in production.
        """
        env_key = cls.ADK_INSTRUCTION_ENV_KEYS.get(agent_name)
        if not env_key:
            return default
        value = os.getenv(env_key)
        if value and value.strip():
            return value.strip()
        return default
