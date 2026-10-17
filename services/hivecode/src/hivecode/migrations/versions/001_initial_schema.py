"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-10-17

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column("github_user_id", sa.Integer(), unique=True, nullable=False),
        sa.Column("github_login", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255)),
        sa.Column("avatar_url", sa.Text()),
        sa.Column("email", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("disabled_at", sa.DateTime(timezone=True)),
    )

    # Sessions
    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.LargeBinary(), unique=True, nullable=False),
        sa.Column("csrf_secret", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("idle_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("ip", postgresql.INET()),
        sa.Column("user_agent", sa.Text()),
    )
    op.create_index("idx_sessions_user_id", "sessions", ["user_id"])

    # GitHub Installations
    op.create_table(
        "github_installations",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column("github_installation_id", sa.Integer(), unique=True, nullable=False),
        sa.Column("account_login", sa.String(255)),
        sa.Column("account_type", sa.String(50), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("suspended_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Repositories
    op.create_table(
        "repositories",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column(
            "installation_id",
            postgresql.UUID(),
            sa.ForeignKey("github_installations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("github_repo_id", sa.Integer(), unique=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("default_branch", sa.String(255), nullable=False, server_default="main"),
        sa.Column("is_private", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("language", sa.String(50)),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_repos_installation_id", "repositories", ["installation_id"])

    # User Repository Grants
    op.create_table(
        "user_repository_grants",
        sa.Column(
            "user_id",
            postgresql.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "repository_id",
            postgresql.UUID(),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("permission", sa.String(20), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Tasks
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "repository_id",
            postgresql.UUID(),
            sa.ForeignKey("repositories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("correlation_id", postgresql.UUID(), unique=True, nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("acceptance_criteria", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("scope", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("required_checks", sa.JSON()),
        sa.Column("base_ref", sa.String(255), nullable=False),
        sa.Column("base_commit_sha", sa.CHAR(40), nullable=False),
        sa.Column("state", sa.String(30), nullable=False, server_default="queued"),
        sa.Column("stage", sa.String(30)),
        sa.Column("outcome", sa.String(30)),
        sa.Column(
            "repair_attempts_used",
            sa.SmallInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("budget", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("usage", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("config_snapshot", sa.JSON(), nullable=False),
        sa.Column("lease_owner", sa.String(255)),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True)),
        sa.Column("cancel_requested_at", sa.DateTime(timezone=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        sa.CheckConstraint(
            "state IN ('queued','running','awaiting_approval,"
            "'cancel_requested','finished','cancelled')",
            name="ck_tasks_state",
        ),
        sa.CheckConstraint(
            "outcome IS NULL OR outcome IN ('verified','failed','blocked',"
            "'partially_verified')",
            name="ck_tasks_outcome",
        ),
        sa.CheckConstraint(
            "(state = 'finished') = (outcome IS NOT NULL)",
            name="ck_tasks_outcome_only_on_finished",
        ),
        sa.CheckConstraint(
            "repair_attempts_used BETWEEN 0 AND 3",
            name="ck_tasks_repair_attempts",
        ),
    )
    op.create_index("idx_tasks_user_id_created_at", "tasks", ["user_id", "created_at"])
    op.create_index("idx_tasks_repository_id", "tasks", ["repository_id"])
    op.create_index("idx_tasks_state", "tasks", ["state"])

    # Task Attempts
    op.create_table(
        "task_attempts",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column(
            "task_id",
            postgresql.UUID(),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attempt_no", sa.SmallInteger(), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column(
            "patch_artifact_id",
            postgresql.UUID(),
            sa.ForeignKey("artifacts.id", ondelete="SET NULL"),
        ),
        sa.Column("patch_sha256", sa.CHAR(64), nullable=False),
        sa.Column("tree_sha", sa.CHAR(40), nullable=False),
        sa.Column("failure_classification", sa.JSON()),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint(
            "task_id", "attempt_no", name="uq_task_attempts_task_attempt_no"
        ),
        sa.CheckConstraint("attempt_no BETWEEN 0 AND 3", name="ck_task_attempts_no"),
    )

    # Check Runs
    op.create_table(
        "check_runs",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column(
            "task_id",
            postgresql.UUID(),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "attempt_id",
            postgresql.UUID(),
            sa.ForeignKey("task_attempts.id", ondelete="CASCADE"),
        ),
        sa.Column("check_key", sa.String(100), nullable=False),
        sa.Column("run_seq", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("exit_code", sa.Integer()),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column("tree_sha", sa.CHAR(40), nullable=False),
        sa.Column("counts", sa.JSON()),
        sa.Column("runner_image_digest", sa.String(255), nullable=False),
        sa.Column("command_id", sa.String(100), nullable=False),
        sa.Column(
            "log_artifact_id",
            postgresql.UUID(),
            sa.ForeignKey("artifacts.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "junit_artifact_id",
            postgresql.UUID(),
            sa.ForeignKey("artifacts.id", ondelete="SET NULL"),
        ),
        sa.Column("flaky_suspected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "attempt_id", "check_key", "run_seq", name="uq_check_runs_attempt_key_seq"
        ),
    )

    # Task Events
    op.create_table(
        "task_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "task_id",
            postgresql.UUID(),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("stage", sa.String(30)),
        sa.Column("attempt_no", sa.SmallInteger()),
        sa.Column("data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("correlation_id", postgresql.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("task_id", "seq", name="uq_task_events_task_seq"),
    )
    op.create_index("idx_task_events_task_id_seq", "task_events", ["task_id", "seq"])

    # Artifacts
    op.create_table(
        "artifacts",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column(
            "task_id",
            postgresql.UUID(),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "attempt_id",
            postgresql.UUID(),
            sa.ForeignKey("task_attempts.id", ondelete="CASCADE"),
        ),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("storage_key", sa.Text(), unique=True, nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.CHAR(64), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("redaction_version", sa.String(20), nullable=False, server_default="v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_artifacts_task_id", "artifacts", ["task_id"])
    op.create_index("idx_artifacts_expires_at", "artifacts", ["expires_at"])

    # Review Findings
    op.create_table(
        "review_findings",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column(
            "task_id",
            postgresql.UUID(),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "attempt_id",
            postgresql.UUID(),
            sa.ForeignKey("task_attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("file_path", sa.String(500)),
        sa.Column("line", sa.Integer()),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("blocks_delivery", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Approvals
    op.create_table(
        "approvals",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column(
            "task_id",
            postgresql.UUID(),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("requested_payload", sa.JSON(), nullable=False),
        sa.Column("payload_hash", sa.CHAR(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "decided_by",
            postgresql.UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Verdicts
    op.create_table(
        "verdicts",
        sa.Column(
            "task_id",
            postgresql.UUID(),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("outcome", sa.String(30), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("policy_version", sa.String(50), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # LLM Calls
    op.create_table(
        "llm_calls",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column(
            "task_id",
            postgresql.UUID(),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "attempt_id",
            postgresql.UUID(),
            sa.ForeignKey("task_attempts.id", ondelete="CASCADE"),
        ),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("prompt_version", sa.String(50), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "transcript_artifact_id",
            postgresql.UUID(),
            sa.ForeignKey("artifacts.id", ondelete="SET NULL"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Pull Requests
    op.create_table(
        "pull_requests",
        sa.Column(
            "task_id",
            postgresql.UUID(),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("github_pr_number", sa.Integer(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("head_branch", sa.String(255), nullable=False),
        sa.Column("head_sha", sa.CHAR(40), nullable=False),
        sa.Column("base_sha", sa.CHAR(40), nullable=False),
        sa.Column("outcome_at_creation", sa.String(30), nullable=False),
        sa.Column("draft", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_by",
            postgresql.UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Idempotency Keys
    op.create_table(
        "idempotency_keys",
        sa.Column(
            "user_id",
            postgresql.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("route", sa.String(255), primary_key=True),
        sa.Column("key", sa.String(255), primary_key=True),
        sa.Column("request_hash", sa.CHAR(64), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Audit Log
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", postgresql.UUID()),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("ip", postgresql.INET()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Webhook Deliveries
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column("github_delivery_id", sa.String(255), unique=True, nullable=False),
        sa.Column("event", sa.String(100), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("webhook_deliveries")
    op.drop_table("audit_log")
    op.drop_table("idempotency_keys")
    op.drop_table("pull_requests")
    op.drop_table("llm_calls")
    op.drop_table("verdicts")
    op.drop_table("approvals")
    op.drop_table("review_findings")
    op.drop_table("artifacts")
    op.drop_table("task_events")
    op.drop_table("check_runs")
    op.drop_table("task_attempts")
    op.drop_table("tasks")
    op.drop_table("user_repository_grants")
    op.drop_table("repositories")
    op.drop_table("github_installations")
    op.drop_table("sessions")
    op.drop_table("users")
