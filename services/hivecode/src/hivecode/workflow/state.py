"""Workflow state — Pydantic model persisted by LangGraph checkpointer."""

from uuid import UUID

from pydantic import BaseModel, Field

from hivecode.agents.schemas import Diagnosis, EditSet


class WorkflowState(BaseModel):
    """State for the workflow graph.

    Persisted by the LangGraph checkpointer after every node.
    Counters that govern safety are not read from the model's state alone:
    the router reads tasks.repair_attempts_used and the frozen
    required_checks from PostgreSQL.
    """

    task_id: UUID
    base_commit_sha: str = ""
    attempt_no: int = 0  # 0..3, derived from DB on every routing decision
    plan: Diagnosis | None = None
    required_checks: list[dict] = Field(default_factory=list)  # frozen at node 3
    current_edit_set: EditSet | None = None
    current_tree_sha: str | None = None
    last_failures: list[dict] = Field(default_factory=list)
    pending_approval_id: UUID | None = None
    stop_reason: str | None = None
    budget_used: dict = Field(default_factory=dict)
