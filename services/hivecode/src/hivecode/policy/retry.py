"""Retry policy — failure classification and repair routing.

Pure functions only. No I/O.
"""

from dataclasses import dataclass
from enum import StrEnum


class FailureClass(StrEnum):
    PRE_EXISTING = "pre_existing"
    ENVIRONMENTAL = "environmental"
    PATCH_RELATED = "patch_related"
    UNKNOWN = "unknown"


@dataclass
class FailureRecord:
    """A single test failure."""

    test_id: str
    message: str
    traceback: str = ""
    file_path: str = ""
    line_number: int = 0


@dataclass
class Classification:
    """Result of failure classification."""

    failure_class: FailureClass
    reason: str
    consumes_repair_attempt: bool


def classify_failure(
    failure: FailureRecord,
    baseline_failures: list[FailureRecord],
    edited_files: list[str],
) -> Classification:
    """Classify a failure using deterministic rules.

    Rules (in order):
    1. pre_existing — same test id failed on base commit baseline
    2. environmental — install/collection failure, OOM, mirror/network errors
    3. patch_related — failing target test, syntax/import error in edited files,
       lint or type error in changed lines
    4. unknown — none of the above (may be reclassified by failure analyst LLM)
    """
    # Rule 1: pre-existing
    for bf in baseline_failures:
        if bf.test_id == failure.test_id:
            return Classification(
                failure_class=FailureClass.PRE_EXISTING,
                reason=f"Test {failure.test_id} failed on base commit baseline",
                consumes_repair_attempt=False,
            )

    # Rule 2: environmental
    env_indicators = [
        "could not find a version",
        "no matching distribution",
        "connection error",
        "timeout",
        "oom",
        "out of memory",
        "killed",
        "collection error",
    ]
    failure_text = f"{failure.message} {failure.traceback}".lower()
    for indicator in env_indicators:
        if indicator in failure_text:
            return Classification(
                failure_class=FailureClass.ENVIRONMENTAL,
                reason=f"Environmental failure detected: {indicator}",
                consumes_repair_attempt=False,
            )

    # Check if failure is in an edited file
    for ef in edited_files:
        if ef in failure.file_path or failure.file_path in ef:
            return Classification(
                failure_class=FailureClass.PATCH_RELATED,
                reason=f"Failure in edited file: {failure.file_path}",
                consumes_repair_attempt=True,
            )

    # Rule 3: patch_related (syntax/import errors)
    patch_indicators = ["syntaxerror", "importerror", "modulenotfounderror"]
    for indicator in patch_indicators:
        if indicator in failure_text:
            return Classification(
                failure_class=FailureClass.PATCH_RELATED,
                reason=f"Patch-related failure: {indicator}",
                consumes_repair_attempt=True,
            )

    # Rule 4: unknown — defaults to patch_related for repair
    # but can never be reclassified to pre_existing by the LLM
    return Classification(
        failure_class=FailureClass.UNKNOWN,
        reason="Failure could not be classified by rules",
        consumes_repair_attempt=True,
    )


def should_stop_no_progress(
    current_patch_sha256: str,
    previous_patch_sha256: str | None,
    current_failures: list[str],
    previous_failures: list[str],
) -> bool:
    """Check if the repair loop has made no progress.

    Stops if:
    - The patch hash is identical to the previous attempt
    - The failing test set is identical across two consecutive attempts
    """
    if previous_patch_sha256 and current_patch_sha256 == previous_patch_sha256:
        return True

    return bool(previous_failures and set(current_failures) == set(previous_failures))


def can_start_repair(
    repair_attempts_used: int,
    max_attempts: int,
    remaining_time_s: float,
    remaining_cost_usd: float,
    min_time_s: float = 180,
    min_cost_usd: float = 0,
) -> tuple[bool, str]:
    """Check if a repair attempt can be started.

    Returns (can_start, reason).
    """
    if repair_attempts_used >= max_attempts:
        return False, "RETRY_BUDGET_EXHAUSTED"

    if remaining_time_s < min_time_s:
        return False, "INSUFFICIENT_TIME_BUDGET"

    if remaining_cost_usd < min_cost_usd:
        return False, "INSUFFICIENT_COST_BUDGET"

    return True, ""
