"""Tests for the verdict engine — the most critical pure function."""

import pytest

from hivecode.policy.verdict import (
    CheckResult,
    CheckStatus,
    Evidence,
    Outcome,
    compute_verdict,
)


class TestComputeVerified:
    """All mandatory checks passed → Verified."""

    def test_all_mandatory_passed(self):
        evidence = Evidence(
            check_results=[
                CheckResult("install", CheckStatus.PASSED, True, "abc123"),
                CheckResult("tests.target", CheckStatus.PASSED, True, "abc123"),
                CheckResult("tests.regression", CheckStatus.PASSED, True, "abc123"),
                CheckResult("lint", CheckStatus.PASSED, True, "abc123"),
            ],
            policy_version="v1.0.0",
        )
        verdict = compute_verdict(evidence)
        assert verdict.outcome == Outcome.VERIFIED
        assert "ALL_MANDATORY_CHECKS_PASSED" in verdict.reasons

    def test_non_mandatory_skipped_still_verified(self):
        evidence = Evidence(
            check_results=[
                CheckResult("install", CheckStatus.PASSED, True, "abc123"),
                CheckResult("tests.target", CheckStatus.PASSED, True, "abc123"),
                CheckResult("typecheck", CheckStatus.SKIPPED, False, "abc123"),
            ],
            policy_version="v1.0.0",
        )
        verdict = compute_verdict(evidence)
        assert verdict.outcome == Outcome.VERIFIED


class TestComputeFailed:
    """Mandatory check failed → Failed."""

    def test_mandatory_check_failed(self):
        evidence = Evidence(
            check_results=[
                CheckResult("install", CheckStatus.PASSED, True, "abc123"),
                CheckResult("tests.target", CheckStatus.FAILED, True, "abc123"),
            ],
            policy_version="v1.0.0",
        )
        verdict = compute_verdict(evidence)
        assert verdict.outcome == Outcome.FAILED
        assert "CHECK_FAILED:tests.target" in verdict.reasons

    def test_mandatory_check_error(self):
        evidence = Evidence(
            check_results=[
                CheckResult("install", CheckStatus.ERROR, True, "abc123"),
            ],
            policy_version="v1.0.0",
        )
        verdict = compute_verdict(evidence)
        assert verdict.outcome == Outcome.FAILED

    def test_mandatory_check_timed_out(self):
        evidence = Evidence(
            check_results=[
                CheckResult("tests.target", CheckStatus.TIMED_OUT, True, "abc123"),
            ],
            policy_version="v1.0.0",
        )
        verdict = compute_verdict(evidence)
        assert verdict.outcome == Outcome.FAILED

    def test_empty_patch(self):
        evidence = Evidence(
            check_results=[],
            is_empty_patch=True,
            policy_version="v1.0.0",
        )
        verdict = compute_verdict(evidence)
        assert verdict.outcome == Outcome.FAILED
        assert "EMPTY_PATCH" in verdict.reasons


class TestComputeBlocked:
    """Blocking condition → Blocked."""

    def test_scope_violation(self):
        evidence = Evidence(
            check_results=[
                CheckResult("install", CheckStatus.PASSED, True, "abc123"),
            ],
            has_scope_violation=True,
            policy_version="v1.0.0",
        )
        verdict = compute_verdict(evidence)
        assert verdict.outcome == Outcome.BLOCKED
        assert "SCOPE_VIOLATION" in verdict.reasons

    def test_blocking_review_finding(self):
        evidence = Evidence(
            check_results=[
                CheckResult("install", CheckStatus.PASSED, True, "abc123"),
            ],
            has_blocking_finding=True,
            policy_version="v1.0.0",
        )
        verdict = compute_verdict(evidence)
        assert verdict.outcome == Outcome.BLOCKED
        assert "REVIEW_FINDING_BLOCKS_DELIVERY" in verdict.reasons

    def test_no_mandatory_checks(self):
        evidence = Evidence(
            check_results=[],
            policy_version="v1.0.0",
        )
        verdict = compute_verdict(evidence)
        assert verdict.outcome == Outcome.BLOCKED
        assert "NO_MANDATORY_CHECKS" in verdict.reasons

    def test_blocking_reasons_listed(self):
        evidence = Evidence(
            check_results=[
                CheckResult("install", CheckStatus.PASSED, True, "abc123"),
            ],
            blocking_reasons=["CLARIFICATION_NEEDED"],
            policy_version="v1.0.0",
        )
        verdict = compute_verdict(evidence)
        assert verdict.outcome == Outcome.BLOCKED
        assert "CLARIFICATION_NEEDED" in verdict.reasons


class TestComputePartiallyVerified:
    """No mandatory failed, at least one passed, at least one non-passed → Partially verified."""

    def test_mandatory_skipped(self):
        evidence = Evidence(
            check_results=[
                CheckResult("install", CheckStatus.PASSED, True, "abc123"),
                CheckResult("tests.target", CheckStatus.PASSED, True, "abc123"),
                CheckResult("typecheck", CheckStatus.SKIPPED, True, "abc123"),
            ],
            policy_version="v1.0.0",
        )
        verdict = compute_verdict(evidence)
        assert verdict.outcome == Outcome.PARTIALLY_VERIFIED

    def test_mandatory_unavailable(self):
        evidence = Evidence(
            check_results=[
                CheckResult("install", CheckStatus.PASSED, True, "abc123"),
                CheckResult("lint", CheckStatus.UNAVAILABLE, True, "abc123"),
            ],
            policy_version="v1.0.0",
        )
        verdict = compute_verdict(evidence)
        assert verdict.outcome == Outcome.PARTIALLY_VERIFIED


class TestVerdictNeverFalselyVerified:
    """Property: a failed mandatory check always implies not Verified."""

    @pytest.mark.parametrize(
        "status", [CheckStatus.FAILED, CheckStatus.ERROR, CheckStatus.TIMED_OUT]
    )
    def test_failed_mandatory_never_verified(self, status):
        evidence = Evidence(
            check_results=[
                CheckResult("install", CheckStatus.PASSED, True, "abc123"),
                CheckResult("tests.target", status, True, "abc123"),
            ],
            policy_version="v1.0.0",
        )
        verdict = compute_verdict(evidence)
        assert verdict.outcome != Outcome.VERIFIED

    @pytest.mark.parametrize(
        "status",
        [CheckStatus.SKIPPED, CheckStatus.UNAVAILABLE, CheckStatus.CANCELLED],
    )
    def test_non_passed_mandatory_never_verified(self, status):
        evidence = Evidence(
            check_results=[
                CheckResult("install", CheckStatus.PASSED, True, "abc123"),
                CheckResult("tests.target", status, True, "abc123"),
            ],
            policy_version="v1.0.0",
        )
        verdict = compute_verdict(evidence)
        assert verdict.outcome != Outcome.VERIFIED
