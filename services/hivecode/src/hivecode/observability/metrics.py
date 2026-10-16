"""Metrics collection for HiveCode.

Tracks: tasks by outcome, repair attempts, stage durations,
queue wait time, sandbox concurrency, LLM tokens and cost.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class MetricValue:
    """A single metric value."""

    type: MetricType
    value: float
    labels: dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """In-memory metrics collector.

    In production, this would push to Prometheus or similar.
    For now, metrics are stored in memory and can be queried.
    """

    def __init__(self):
        self._metrics: dict[str, list[MetricValue]] = defaultdict(list)

    def increment(self, name: str, value: float = 1, **labels: str) -> None:
        """Increment a counter metric."""
        self._metrics[name].append(
            MetricValue(type=MetricType.COUNTER, value=value, labels=labels)
        )

    def gauge(self, name: str, value: float, **labels: str) -> None:
        """Set a gauge metric."""
        self._metrics[name].append(
            MetricValue(type=MetricType.GAUGE, value=value, labels=labels)
        )

    def histogram(self, name: str, value: float, **labels: str) -> None:
        """Record a histogram observation."""
        self._metrics[name].append(
            MetricValue(type=MetricType.HISTOGRAM, value=value, labels=labels)
        )

    def get_metrics(self) -> dict:
        """Get all collected metrics."""
        return {
            name: [
                {"type": m.type.value, "value": m.value, "labels": m.labels}
                for m in values
            ]
            for name, values in self._metrics.items()
        }

    # Convenience methods for HiveCode-specific metrics

    def record_task_outcome(self, outcome: str, reason: str = "") -> None:
        """Record a task outcome."""
        self.increment("tasks_total", outcome=outcome, reason=reason)

    def record_repair_attempt(self, task_id: str, attempt_no: int) -> None:
        """Record a repair attempt."""
        self.increment("repair_attempts_total", task_id=task_id, attempt_no=attempt_no)

    def record_stage_duration(self, stage: str, duration_ms: float) -> None:
        """Record a stage duration."""
        self.histogram("stage_duration_ms", duration_ms, stage=stage)

    def record_llm_call(self, role: str, tokens: int, cost_usd: float) -> None:
        """Record an LLM API call."""
        self.increment("llm_calls_total", role=role)
        self.increment("llm_tokens_total", value=tokens, role=role)
        self.increment("llm_cost_usd_total", value=cost_usd, role=role)

    def record_sandbox_job(self, status: str, duration_ms: float) -> None:
        """Record a sandbox job."""
        self.increment("sandbox_jobs_total", status=status)
        self.histogram("sandbox_duration_ms", duration_ms, status=status)


# Global metrics instance
metrics = MetricsCollector()
