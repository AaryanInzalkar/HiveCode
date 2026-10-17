"""Celery tasks for workflow execution."""

from typing import Any

from celery import shared_task


@shared_task(bind=True, max_retries=3)
def run_workflow(self: Any, task_id: str) -> dict[str, str]:
    """Execute the full workflow for a task.

    This is the main entry point for task execution.
    The workflow is a LangGraph StateGraph with checkpointing.
    """
    # TODO: Implement LangGraph workflow execution
    # For now, this is a placeholder that will be implemented in Phase 2+
    print(f"Starting workflow for task {task_id}")
    return {"task_id": task_id, "status": "started"}


@shared_task
def run_baseline(task_id: str) -> None:
    """Run baseline tests on the unmodified repository."""
    # TODO: Implement in Phase 2


@shared_task
def run_diagnosis(task_id: str) -> None:
    """Run diagnosis and planning."""
    # TODO: Implement in Phase 2


@shared_task
def generate_patch(task_id: str, attempt_no: int) -> None:
    """Generate a patch for the given attempt."""
    # TODO: Implement in Phase 3


@shared_task
def validate_patch(task_id: str, attempt_id: str) -> None:
    """Validate a patch in the sandbox."""
    # TODO: Implement in Phase 3


@shared_task
def run_review(task_id: str, attempt_id: str) -> None:
    """Run independent review on the final diff."""
    # TODO: Implement in Phase 4


@shared_task
def compute_verdict(task_id: str) -> None:
    """Compute the final verdict from evidence."""
    # TODO: Implement in Phase 4


@shared_task
def deliver_task(task_id: str) -> None:
    """Deliver the result — render report, create PR if eligible."""
    # TODO: Implement in Phase 4
