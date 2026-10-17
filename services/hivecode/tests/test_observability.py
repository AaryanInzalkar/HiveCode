"""Tests for observability components."""

import logging

from hivecode.observability.logging import RedactingFilter, StructuredLogger
from hivecode.observability.metrics import MetricsCollector


class TestRedactingFilter:
    def test_redacts_sensitive_keys(self):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg={"api_key": "secret123", "message": "hello"},
            args=(),
            exc_info=None,
        )
        filter = RedactingFilter()
        filter.filter(record)

        assert record.msg["api_key"] == "***REDACTED***"
        assert record.msg["message"] == "hello"

    def test_redacts_nested(self):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg={"data": {"password": "secret", "user": "john"}},
            args=(),
            exc_info=None,
        )
        filter = RedactingFilter()
        filter.filter(record)

        assert record.msg["data"]["password"] == "***REDACTED***"
        assert record.msg["data"]["user"] == "john"


class TestStructuredLogger:
    def test_log_output_is_json(self, caplog):
        caplog.set_level(logging.INFO)
        logger = StructuredLogger("test")
        logger.logger.propagate = True
        logger.logger.setLevel(logging.INFO)
        logger.info("test message", task_id="123")

        # The log record should have correlation_id and task_id
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert hasattr(record, "correlation_id")
        assert hasattr(record, "task_id")


class TestMetricsCollector:
    def test_increment(self):
        collector = MetricsCollector()
        collector.increment("test_counter", 1, label="value")

        metrics = collector.get_metrics()
        assert "test_counter" in metrics
        assert metrics["test_counter"][0]["value"] == 1

    def test_gauge(self):
        collector = MetricsCollector()
        collector.gauge("test_gauge", 42.0)

        metrics = collector.get_metrics()
        assert metrics["test_gauge"][0]["value"] == 42.0

    def test_histogram(self):
        collector = MetricsCollector()
        collector.histogram("test_histogram", 100.0)
        collector.histogram("test_histogram", 200.0)

        metrics = collector.get_metrics()
        assert len(metrics["test_histogram"]) == 2

    def test_record_task_outcome(self):
        collector = MetricsCollector()
        collector.record_task_outcome("verified")

        metrics = collector.get_metrics()
        assert "tasks_total" in metrics

    def test_record_llm_call(self):
        collector = MetricsCollector()
        collector.record_llm_call("analyst", 1000, 0.01)

        metrics = collector.get_metrics()
        assert "llm_calls_total" in metrics
        assert "llm_tokens_total" in metrics
        assert "llm_cost_usd_total" in metrics
