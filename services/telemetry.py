"""
Telemetry Service — Monitoring, Latency, and SLA Metrics tracking.

This service collects structured metrics about agent execution, fallback chains,
tool invocation frequency, and SLA compliance to guarantee production reliability.
"""

import logging
import time
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class AgentTelemetry:
    """Collects and aggregates runtime metrics for ADK agents."""

    def __init__(self):
        self.metrics = {
            "invocations": 0,
            "fallback_activations": 0,
            "sla_breaches": 0,
            "latency_records": [],
            "agent_usage": {},
            "tool_calls": {},
            "session_reuses": 0,
            "session_creates": 0,
            "transient_retries": 0,
        }
        self.SLA_LIMIT_SECONDS = 15.0  # 15s max SLA limit for agent responses

    def record_invocation(self, agent_name: str) -> None:
        """Record a call to an agent."""
        self.metrics["invocations"] += 1
        self.metrics["agent_usage"][agent_name] = self.metrics["agent_usage"].get(agent_name, 0) + 1

    def record_latency(self, duration_seconds: float) -> None:
        """Record response latency and check against SLA limit."""
        self.metrics["latency_records"].append(duration_seconds)
        if duration_seconds > self.SLA_LIMIT_SECONDS:
            self.metrics["sla_breaches"] += 1
            logger.warning(
                "🚨 SLA Breach detected! Response time was %.2fs (limit %.2fs)",
                duration_seconds,
                self.SLA_LIMIT_SECONDS,
            )

    def record_fallback(self, task: str, failed_model: str, fallback_model: str) -> None:
        """Record model fallback event."""
        self.metrics["fallback_activations"] += 1
        logger.info(
            "🔄 Model fallback triggered for task '%s': %s -> %s",
            task,
            failed_model,
            fallback_model,
        )

    def record_tool_call(self, tool_name: str) -> None:
        """Record tool call frequency."""
        self.metrics["tool_calls"][tool_name] = self.metrics["tool_calls"].get(tool_name, 0) + 1

    def record_session(self, reused: bool) -> None:
        """Track session persistence and reuse."""
        if reused:
            self.metrics["session_reuses"] += 1
        else:
            self.metrics["session_creates"] += 1

    def record_transient_retry(self, error_msg: str, attempt: int) -> None:
        """Track transient error retries."""
        self.metrics["transient_retries"] += 1
        logger.info(
            "⏳ Transient retry attempt %d due to: %s",
            attempt,
            error_msg[:100],
        )

    def get_summary(self) -> Dict[str, Any]:
        """Aggregate and return current execution metrics."""
        latencies = self.metrics["latency_records"]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0.0
        
        return {
            "total_runs": self.metrics["invocations"],
            "session_reuse_ratio": (
                self.metrics["session_reuses"] / 
                (self.metrics["session_reuses"] + self.metrics["session_creates"])
                if (self.metrics["session_reuses"] + self.metrics["session_creates"]) > 0 
                else 0.0
            ),
            "fallback_rate": (
                self.metrics["fallback_activations"] / self.metrics["invocations"]
                if self.metrics["invocations"] > 0
                else 0.0
            ),
            "sla_compliance": (
                (self.metrics["invocations"] - self.metrics["sla_breaches"]) / self.metrics["invocations"]
                if self.metrics["invocations"] > 0
                else 1.0
            ),
            "average_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "agent_frequency": self.metrics["agent_usage"],
            "popular_tools": dict(sorted(self.metrics["tool_calls"].items(), key=lambda item: item[1], reverse=True)[:5]),
            "retry_events": self.metrics["transient_retries"],
        }


# Global telemetry collector
telemetry = AgentTelemetry()
