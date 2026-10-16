"""Tests for the report builder."""

from datetime import datetime, timezone
from uuid import uuid4

from hivecode.reports.builder import ReportBuilder, ReportSection, VerificationReport


class TestReportBuilder:
    def test_build_report(self):
        builder = ReportBuilder()
        report = builder.build(
            task_id=uuid4(),
            outcome="verified",
            policy_version="v1.0.0",
            title="Fix duplicate orders",
            objective="Duplicates appear in order listing",
            changed_files=["src/orders/service.py"],
            check_results=[
                {"check_key": "install", "status": "passed"},
                {"check_key": "tests", "status": "passed"},
            ],
            attempts_used=1,
            max_attempts=4,
            cost_usd=0.42,
            duration_s=135.0,
            verdict_reasons=["ALL_MANDATORY_CHECKS_PASSED"],
            evidence={},
        )

        assert report.outcome == "verified"
        assert len(report.sections) == 5

    def test_to_markdown(self):
        builder = ReportBuilder()
        report = builder.build(
            task_id=uuid4(),
            outcome="verified",
            policy_version="v1.0.0",
            title="Test fix",
            objective="Test objective",
            changed_files=["src/test.py"],
            check_results=[{"check_key": "tests", "status": "passed"}],
            attempts_used=1,
            max_attempts=4,
            cost_usd=0.10,
            duration_s=60.0,
            verdict_reasons=["ALL_MANDATORY_CHECKS_PASSED"],
            evidence={},
        )

        md = report.to_markdown()

        assert "# Verification Report" in md
        assert "verified" in md
        assert "src/test.py" in md
        assert "ALL_MANDATORY_CHECKS_PASSED" in md

    def test_build_pr_body(self):
        builder = ReportBuilder()
        report = builder.build(
            task_id=uuid4(),
            outcome="verified",
            policy_version="v1.0.0",
            title="Fix bug",
            objective="Bug description",
            changed_files=["src/bug.py"],
            check_results=[{"check_key": "tests", "status": "passed"}],
            attempts_used=1,
            max_attempts=4,
            cost_usd=0.20,
            duration_s=90.0,
            verdict_reasons=["ALL_MANDATORY_CHECKS_PASSED"],
            evidence={},
        )

        body = builder.build_pr_body("Fix bug", report, diff_url="https://example.com/diff")

        assert "HiveCode Verification Report" in body
        assert "verified" in body
        assert "https://example.com/diff" in body
        assert "does not guarantee correctness" in body

    def test_status_icons(self):
        builder = ReportBuilder()
        assert builder._status_icon("passed") == "✓"
        assert builder._status_icon("failed") == "✗"
        assert builder._status_icon("error") == "⚠"
        assert builder._status_icon("unknown") == "?"
