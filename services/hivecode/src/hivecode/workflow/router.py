"""Workflow router — deterministic routing decisions.

The router reads tasks.repair_attempts_used and the frozen
required_checks from PostgreSQL. It is the ONLY place where
routing decisions are made.
"""

from hivecode.policy.retry import (
    FailureClass,
    can_start_repair,
    should_stop_no_progress,
)
from hivecode.workflow.state import WorkflowState


def route_after_evaluate(
    state: WorkflowState,
    check_results: list[dict],
) -> str:
    """Route after check evaluation.

    Returns:
        "review" — all mandatory checks passed
        "classify" — mandatory check failed
        "verdict" — no mandatory checks or other blocking condition
    """
    mandatory = [c for c in check_results if c.get("is_mandatory")]

    if not mandatory:
        return "verdict"

    # Check if any mandatory check failed
    has_failure = any(
        c.get("status") in ("failed", "error", "timed_out") for c in mandatory
    )

    if has_failure:
        return "classify"

    return "review"


def route_after_classify(
    state: WorkflowState,
    classification: dict,
    repair_attempts_used: int,
    max_attempts: int = 3,
) -> str:
    """Route after failure classification.

    Returns:
        "patch" — start a repair attempt
        "verdict" — stop and compute verdict
    """
    failure_class = classification.get("failure_class")

    # Pre-existing failures don't consume repair attempts
    if failure_class == FailureClass.PRE_EXISTING.value:
        return "verdict"

    # Environmental failures get a bounded re-run, not a repair
    if failure_class == FailureClass.ENVIRONMENTAL.value:
        return "verdict"  # TODO: Implement re-run logic

    # Check no-progress stop
    if should_stop_no_progress(
        current_patch_sha256=classification.get("patch_sha256", ""),
        previous_patch_sha256=classification.get("previous_patch_sha256"),
        current_failures=classification.get("current_failures", []),
        previous_failures=classification.get("previous_failures", []),
    ):
        return "verdict"

    # Check if we can start a repair
    can_start, _ = can_start_repair(
        repair_attempts_used=repair_attempts_used,
        max_attempts=max_attempts,
        remaining_time_s=classification.get("remaining_time_s", 0),
        remaining_cost_usd=classification.get("remaining_cost_usd", 0),
    )

    if not can_start:
        return "verdict"

    return "patch"


def route_after_review(
    state: WorkflowState,
    review_findings: list[dict],
    repair_attempts_used: int,
    max_attempts: int = 3,
) -> str:
    """Route after independent review.

    Returns:
        "verdict" — proceed to verdict
        "patch" — blocking finding with repair budget left
    """
    blocking = [f for f in review_findings if f.get("blocks_delivery")]

    if not blocking:
        return "verdict"

    # Check if we have repair budget left
    if repair_attempts_used < max_attempts:
        return "patch"

    return "verdict"
