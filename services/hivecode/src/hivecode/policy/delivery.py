"""Delivery policy — determines when and how results are delivered.

Pure functions only. No I/O.
"""

from dataclasses import dataclass
from enum import Enum


class DeliveryMode(str, Enum):
    PR = "pr"
    REPORT = "report"
    DRAFT_PR = "draft_pr"


class DeliveryDecision(str, Enum):
    CREATE_PR = "create_pr"
    CREATE_DRAFT = "create_draft"
    REPORT_ONLY = "report_only"
    NO_DELIVERY = "no_delivery"


@dataclass
class DeliveryConfig:
    """Configuration for task delivery."""

    mode: DeliveryMode = DeliveryMode.PR
    create_pr_for_non_verified: bool = False  # Requires approval
    auto_merge: bool = False  # Never in V1


def compute_delivery_decision(
    outcome: str,
    config: DeliveryConfig,
    has_pr: bool = False,
    pr_eligible: bool = False,
) -> DeliveryDecision:
    """Compute the delivery decision based on outcome and config.

    Args:
        outcome: The task outcome (verified, failed, blocked, partially_verified)
        config: Delivery configuration
        has_pr: Whether a PR already exists for this task
        pr_eligible: Whether the API says PR creation is eligible

    Returns:
        DeliveryDecision
    """
    if has_pr:
        return DeliveryDecision.NO_DELIVERY

    if config.mode == DeliveryMode.REPORT:
        return DeliveryDecision.REPORT_ONLY

    if outcome == "verified":
        if pr_eligible:
            return DeliveryDecision.CREATE_PR
        return DeliveryDecision.REPORT_ONLY

    if outcome == "partially_verified":
        if config.create_pr_for_non_verified and pr_eligible:
            return DeliveryDecision.CREATE_DRAFT
        return DeliveryDecision.REPORT_ONLY

    # Failed or blocked — no PR
    return DeliveryDecision.NO_DELIVERY


def should_create_pr(
    outcome: str,
    config: DeliveryConfig,
    has_blocking_finding: bool = False,
    has_scope_violation: bool = False,
    approval_granted: bool = False,
) -> bool:
    """Determine whether a pull request should be created.

    A PR is only created when:
    1. The outcome is Verified, OR
    2. The outcome is Partially verified AND the user approved creating a draft PR
    3. There are no blocking findings
    4. There are no scope violations
    """
    if has_scope_violation:
        return False

    if has_blocking_finding and not approval_granted:
        return False

    if outcome == "verified":
        return True

    if outcome == "partially_verified" and config.create_pr_for_non_verified:
        return approval_granted

    return False
