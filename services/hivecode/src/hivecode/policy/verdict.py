"""Verdict engine — computes the final task outcome from recorded evidence.

Pure function. No I/O. No LLM text.

The verdict engine is the ONLY code path that can set outcome = 'verified'.
Model-written summaries are never an input to the outcome.
"""

from dataclasses import dataclass, field
from enum import Enum


class Outcome(str, Enum):
    VERIFIED = "verified"
    FAILED = "failed"
    BLOCKED = "blocked"
    PARTIALLY_VERIFIED = "partially_verified"


class CheckStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    TIMED_OUT = "timed_out"
    SKIPPED = "skipped"
    UNAVAILABLE = "unavailable"
    CANCELLED = "cancelled"


@dataclass
class CheckResult:
    """A single check run result."""

    check_key: str
    status: CheckStatus
    is_mandatory: bool
    tree_sha: str


@dataclass
class Evidence:
    """All evidence for a task's final attempt."""

    check_results: list[CheckResult] = field(default_factory=list)
    has_scope_violation: bool = False
    has_blocking_finding: bool = False
    is_empty_patch: bool = False
    blocking_reasons: list[str] = field(default_factory=list)
    policy_version: str = "v1.0.0"


@dataclass
class Verdict:
    """The computed verdict."""

    outcome: Outcome
    reasons: list[str]
    evidence: Evidence


def compute_verdict(evidence: Evidence) -> Verdict:
    """Compute the verdict from evidence. Pure function, no I/O.

    Evaluation is ordered; the first matching rule decides.

    Order:
    1. Blocked — blocking condition recorded
    2. Failed — primary gate failed, mandatory check failed, empty patch, or budget exhausted
    3. Partially verified — no mandatory failed, at least one passed, at least one non-passed
    4. Verified — every mandatory check passed
    """
    # Rule 1: Blocked
    if evidence.blocking_reasons:
        return Verdict(
            outcome=Outcome.BLOCKED,
            reasons=evidence.blocking_reasons,
            evidence=evidence,
        )

    if evidence.has_scope_violation:
        return Verdict(
            outcome=Outcome.BLOCKED,
            reasons=["SCOPE_VIOLATION"],
            evidence=evidence,
        )

    if evidence.has_blocking_finding:
        return Verdict(
            outcome=Outcome.BLOCKED,
            reasons=["REVIEW_FINDING_BLOCKS_DELIVERY"],
            evidence=evidence,
        )

    # Rule 2: Failed
    if evidence.is_empty_patch:
        return Verdict(
            outcome=Outcome.FAILED,
            reasons=["EMPTY_PATCH"],
            evidence=evidence,
        )

    # Check mandatory checks
    mandatory_checks = [c for c in evidence.check_results if c.is_mandatory]

    if not mandatory_checks:
        return Verdict(
            outcome=Outcome.BLOCKED,
            reasons=["NO_MANDATORY_CHECKS"],
            evidence=evidence,
        )

    for check in mandatory_checks:
        if check.status in (CheckStatus.FAILED, CheckStatus.ERROR, CheckStatus.TIMED_OUT):
            return Verdict(
                outcome=Outcome.FAILED,
                reasons=[f"CHECK_FAILED:{check.check_key}"],
                evidence=evidence,
            )

    # Rule 3: Partially verified
    has_non_passed = any(
        c.status
        in (
            CheckStatus.SKIPPED,
            CheckStatus.UNAVAILABLE,
            CheckStatus.CANCELLED,
        )
        for c in mandatory_checks
    )

    if has_non_passed:
        return Verdict(
            outcome=Outcome.PARTIALLY_VERIFIED,
            reasons=["MANDATORY_CHECK_NOT_PASSED"],
            evidence=evidence,
        )

    # Rule 4: Verified
    all_passed = all(c.status == CheckStatus.PASSED for c in mandatory_checks)
    if all_passed:
        return Verdict(
            outcome=Outcome.VERIFIED,
            reasons=["ALL_MANDATORY_CHECKS_PASSED"],
            evidence=evidence,
        )

    # Fallback (should not reach here)
    return Verdict(
        outcome=Outcome.FAILED,
        reasons=["UNEXPECTED_STATE"],
        evidence=evidence,
    )
