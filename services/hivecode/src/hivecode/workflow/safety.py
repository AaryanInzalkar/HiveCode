"""Safety controls — kill switch, budget enforcement, and stop conditions.

These are the hard limits that cannot be overridden by the LLM or prompts.
"""

import time
from dataclasses import dataclass, field
from enum import Enum


class StopReason(str, Enum):
    """Reasons a task can stop."""

    # Blocking
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED"
    UNSUPPORTED_REPOSITORY = "UNSUPPORTED_REPOSITORY"
    SCOPE_VIOLATION = "SCOPE_VIOLATION"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVAL_EXPIRED = "APPROVAL_EXPIRED"
    NOT_REPRODUCIBLE = "NOT_REPRODUCIBLE"
    ENVIRONMENT_UNSTABLE = "ENVIRONMENT_UNSTABLE"
    NO_MANDATORY_CHECKS = "NO_MANDATORY_CHECKS"

    # Failure
    RETRY_BUDGET_EXHAUSTED = "RETRY_BUDGET_EXHAUSTED"
    EMPTY_PATCH = "EMPTY_PATCH"

    # Service
    SERVICE_SUSPENDED = "SERVICE_SUSPENDED"

    # Success
    VERIFIED = "VERIFIED"
    COMPLETED = "COMPLETED"


@dataclass
class Budget:
    """Task budget tracking."""

    max_time_s: int = 1800  # 30 minutes
    max_cost_usd: float = 5.00
    max_tokens: int = 100000

    time_used_s: float = 0.0
    cost_used_usd: float = 0.0
    tokens_used: int = 0

    @property
    def remaining_time_s(self) -> float:
        return max(0, self.max_time_s - self.time_used_s)

    @property
    def remaining_cost_usd(self) -> float:
        return max(0, self.max_cost_usd - self.cost_used_usd)

    def can_continue(self, min_time_s: float = 180, min_cost_usd: float = 0) -> bool:
        """Check if the task has enough budget to continue."""
        return (
            self.remaining_time_s >= min_time_s
            and self.remaining_cost_usd >= min_cost_usd
        )


@dataclass
class KillSwitch:
    """Global kill switch state."""

    active: bool = False
    activated_at: float | None = None
    reason: str = ""

    def activate(self, reason: str):
        """Activate the kill switch."""
        self.active = True
        self.activated_at = time.time()
        self.reason = reason

    def deactivate(self):
        """Deactivate the kill switch."""
        self.active = False
        self.activated_at = None
        self.reason = ""


class BudgetEnforcer:
    """Enforces task budgets and stop conditions."""

    def __init__(self, budget: Budget):
        self.budget = budget
        self.kill_switch = KillSwitch()

    def check_can_continue(self) -> tuple[bool, str | None]:
        """Check if the task can continue.

        Returns (can_continue, stop_reason).
        """
        # Check kill switch
        if self.kill_switch.active:
            return False, StopReason.SERVICE_SUSPENDED.value

        # Check time budget
        if self.budget.remaining_time_s <= 0:
            return False, StopReason.RETRY_BUDGET_EXHAUSTED.value

        # Check cost budget
        if self.budget.remaining_cost_usd <= 0:
            return False, StopReason.RETRY_BUDGET_EXHAUSTED.value

        return True, None

    def check_can_start_repair(
        self,
        repair_attempts_used: int,
        max_attempts: int = 3,
    ) -> tuple[bool, str | None]:
        """Check if a repair attempt can be started.

        Returns (can_start, stop_reason).
        """
        can_continue, reason = self.check_can_continue()
        if not can_continue:
            return False, reason

        if repair_attempts_used >= max_attempts:
            return False, StopReason.RETRY_BUDGET_EXHAUSTED.value

        if not self.budget.can_continue(min_time_s=180):
            return False, StopReason.RETRY_BUDGET_EXHAUSTED.value

        return True, None

    def record_usage(self, time_s: float, cost_usd: float, tokens: int = 0):
        """Record resource usage."""
        self.budget.time_used_s += time_s
        self.budget.cost_used_usd += cost_usd
        self.budget.tokens_used += tokens
