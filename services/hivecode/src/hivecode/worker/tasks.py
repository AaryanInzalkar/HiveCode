"""Celery tasks for workflow execution."""

from celery import shared_task


@shared_task(bind=True, max_retries=3)
def run_workflow(self, task_id: str):
    """Execute the full workflow for a task.

    This is the main entry point for task execution.
    The workflow is a LangGraph StateGraph with checkpointing.
    """
    # TODO: Implement LangGraph workflow execution
    # For now, this is a placeholder that will be implemented in Phase 2+
    print(f"Starting workflow for task {task_id}")
    return {"task_id": task_id, "status": "started"}


@shared_task
def run_baseline(task_id: str):
    """Run baseline tests on the unmodified repository."""
    # TODO: Implement in Phase 2
    pass


@shared_task
def run_diagnosis(task_id: str):
    """Run diagnosis and planning."""
    # TODO: Implement in Phase 2
    pass


@shared_task
def generate_patch(task_id: str, attempt_no: int):
    """Generate a patch for the given attempt."""
    # TODO: Implement in Phase 3
    pass


@shared_task
def validate_patch(task_id: str, attempt_id: str):
    """Validate a patch in the sandbox."""
    # TODO: Implement in Phase 3
    pass


@shared_task
def run_review(task_id: str, attempt_id: str):
    """Run independent review on the final diff."""
    # TODO: Implement in Phase 4
    pass


@shared_task
def compute_verdict(task_id: str):
    """Compute the final verdict from evidence."""
    # TODO: Implement in Phase 4
    pass


@shared_task
def deliver_task(task_id: str):
    """Deliver the result — render report, create PR if eligible."""
    # TODO: Implement in Phase 4
    pass
