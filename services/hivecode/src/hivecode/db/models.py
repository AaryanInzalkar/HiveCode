"""SQLAlchemy ORM models for HiveCode."""

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import CHAR, INET, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hivecode.db.base import Base


class TaskState(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    CANCEL_REQUESTED = "cancel_requested"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class TaskOutcome(str, enum.Enum):
    VERIFIED = "verified"
    FAILED = "failed"
    BLOCKED = "blocked"
    PARTIALLY_VERIFIED = "partially_verified"


class TaskStage(str, enum.Enum):
    INSPECT = "inspect"
    BASELINE = "baseline"
    DIAGNOSE = "diagnose"
    REPRODUCE = "reproduce"
    PATCH = "patch"
    VALIDATE = "validate"
    CLASSIFY = "classify"
    REPAIR = "repair"
    REVIEW = "review"
    VERDICT = "verdict"
    DELIVER = "deliver"


class CheckStatus(str, enum.Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    TIMED_OUT = "timed_out"
    SKIPPED = "skipped"
    UNAVAILABLE = "unavailable"
    CANCELLED = "cancelled"


class AttemptKind(str, enum.Enum):
    INITIAL = "initial"
    REPAIR = "repair"


class AttemptStatus(str, enum.Enum):
    RUNNING = "running"
    VALIDATED = "validated"
    FAILED = "failed"
    ABANDONED = "abandoned"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalActionType(str, enum.Enum):
    SCOPE_EXPANSION = "scope_expansion"
    PR_NONVERIFIED = "pr_nonverified"
    TEST_MODIFICATION = "test_modification"
    PROTECTED_PATH = "protected_path"


class ReviewSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ArtifactKind(str, enum.Enum):
    DIFF = "diff"
    PLAN = "plan"
    DIAGNOSIS = "diagnosis"
    LOG = "log"
    JUNIT = "junit"
    REPORT = "report"
    WORKSPACE = "workspace"
    TRANSCRIPT = "transcript"


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID, primary_key=True)
    github_user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    github_login: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    sessions: Mapped[list["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    tasks: Mapped[list["Task"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(PG_UUID, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[bytes] = mapped_column(unique=True, nullable=False)
    csrf_secret: Mapped[bytes] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    idle_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    absolute_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ip: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="sessions")


class GitHubInstallation(Base):
    __tablename__ = "github_installations"

    id: Mapped[UUID] = mapped_column(PG_UUID, primary_key=True)
    github_installation_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    account_login: Mapped[str] = mapped_column(String(255))
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)
    permissions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    repositories: Mapped[list["Repository"]] = relationship(back_populates="installation", cascade="all, delete-orphan")


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[UUID] = mapped_column(PG_UUID, primary_key=True)
    installation_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("github_installations.id", ondelete="CASCADE"), nullable=False)
    github_repo_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(255), nullable=False, default="main")
    is_private: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    language: Mapped[str | None] = mapped_column(String(50))
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    installation: Mapped[GitHubInstallation] = relationship(back_populates="repositories")
    tasks: Mapped[list["Task"]] = relationship(back_populates="repository")


class UserRepositoryGrant(Base):
    __tablename__ = "user_repository_grants"
    __table_args__ = (UniqueConstraint("user_id", "repository_id"),)

    user_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    repository_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("repositories.id", ondelete="CASCADE"), primary_key=True)
    permission: Mapped[str] = mapped_column(String(20), nullable=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "state IN ('queued','running','awaiting_approval','cancel_requested','finished','cancelled')",
            name="ck_tasks_state",
        ),
        CheckConstraint(
            "outcome IS NULL OR outcome IN ('verified','failed','blocked','partially_verified')",
            name="ck_tasks_outcome",
        ),
        CheckConstraint(
            "(state = 'finished') = (outcome IS NOT NULL)",
            name="ck_tasks_outcome_only_on_finished",
        ),
        CheckConstraint(
            "repair_attempts_used BETWEEN 0 AND 3",
            name="ck_tasks_repair_attempts",
        ),
        Index("idx_tasks_user_id_created_at", "user_id", "created_at"),
        Index("idx_tasks_repository_id", "repository_id"),
        Index("idx_tasks_state", "state"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    repository_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("repositories.id", ondelete="RESTRICT"), nullable=False)
    correlation_id: Mapped[UUID] = mapped_column(PG_UUID, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    acceptance_criteria: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    scope: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    required_checks: Mapped[list | None] = mapped_column(JSON)
    base_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    base_commit_sha: Mapped[str] = mapped_column(CHAR(40), nullable=False)
    state: Mapped[str] = mapped_column(String(30), nullable=False, default="queued")
    stage: Mapped[str | None] = mapped_column(String(30))
    outcome: Mapped[str | None] = mapped_column(String(30))
    repair_attempts_used: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    budget: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    usage: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    config_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    lease_owner: Mapped[str | None] = mapped_column(String(255))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped[User] = relationship(back_populates="tasks")
    repository: Mapped[Repository] = relationship(back_populates="tasks")
    attempts: Mapped[list["TaskAttempt"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    events: Mapped[list["TaskEvent"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    artifacts: Mapped[list["Artifact"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    review_findings: Mapped[list["ReviewFinding"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    approvals: Mapped[list["Approval"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    llm_calls: Mapped[list["LLMCall"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    verdict: Mapped["Verdict | None"] = relationship(back_populates="task", uselist=False, cascade="all, delete-orphan")
    pull_request: Mapped["PullRequest | None"] = relationship(back_populates="task", uselist=False, cascade="all, delete-orphan")


class TaskAttempt(Base):
    __tablename__ = "task_attempts"
    __table_args__ = (
        UniqueConstraint("task_id", "attempt_no", name="uq_task_attempts_task_attempt_no"),
        CheckConstraint("attempt_no BETWEEN 0 AND 3", name="ck_task_attempts_no"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID, primary_key=True)
    task_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    attempt_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    patch_artifact_id: Mapped[UUID | None] = mapped_column(PG_UUID, ForeignKey("artifacts.id", ondelete="SET NULL"))
    patch_sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    tree_sha: Mapped[str] = mapped_column(CHAR(40), nullable=False)
    failure_classification: Mapped[dict | None] = mapped_column(JSON)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    task: Mapped[Task] = relationship(back_populates="attempts")
    check_runs: Mapped[list["CheckRun"]] = relationship(back_populates="attempt", cascade="all, delete-orphan")
    review_findings: Mapped[list["ReviewFinding"]] = relationship(back_populates="attempt", cascade="all, delete-orphan")


class CheckRun(Base):
    __tablename__ = "check_runs"
    __table_args__ = (
        UniqueConstraint("attempt_id", "check_key", "run_seq", name="uq_check_runs_attempt_key_seq"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID, primary_key=True)
    task_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    attempt_id: Mapped[UUID | None] = mapped_column(PG_UUID, ForeignKey("task_attempts.id", ondelete="CASCADE"))
    check_key: Mapped[str] = mapped_column(String(100), nullable=False)
    run_seq: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    exit_code: Mapped[int | None] = mapped_column(Integer)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    tree_sha: Mapped[str] = mapped_column(CHAR(40), nullable=False)
    counts: Mapped[dict | None] = mapped_column(JSON)
    runner_image_digest: Mapped[str] = mapped_column(String(255), nullable=False)
    command_id: Mapped[str] = mapped_column(String(100), nullable=False)
    log_artifact_id: Mapped[UUID | None] = mapped_column(PG_UUID, ForeignKey("artifacts.id", ondelete="SET NULL"))
    junit_artifact_id: Mapped[UUID | None] = mapped_column(PG_UUID, ForeignKey("artifacts.id", ondelete="SET NULL"))
    flaky_suspected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    attempt: Mapped[TaskAttempt | None] = relationship(back_populates="check_runs")


class TaskEvent(Base):
    __tablename__ = "task_events"
    __table_args__ = (
        UniqueConstraint("task_id", "seq", name="uq_task_events_task_seq"),
        Index("idx_task_events_task_id_seq", "task_id", "seq"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    stage: Mapped[str | None] = mapped_column(String(30))
    attempt_no: Mapped[int | None] = mapped_column(SmallInteger)
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    correlation_id: Mapped[UUID] = mapped_column(PG_UUID, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task: Mapped[Task] = relationship(back_populates="events")


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[UUID] = mapped_column(PG_UUID, primary_key=True)
    task_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    attempt_id: Mapped[UUID | None] = mapped_column(PG_UUID, ForeignKey("task_attempts.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    redaction_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    task: Mapped[Task] = relationship(back_populates="artifacts")


class ReviewFinding(Base):
    __tablename__ = "review_findings"

    id: Mapped[UUID] = mapped_column(PG_UUID, primary_key=True)
    task_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    attempt_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("task_attempts.id", ondelete="CASCADE"), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(500))
    line: Mapped[int | None] = mapped_column(Integer)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    blocks_delivery: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task: Mapped[Task] = relationship(back_populates="review_findings")
    attempt: Mapped[TaskAttempt] = relationship(back_populates="review_findings")


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[UUID] = mapped_column(PG_UUID, primary_key=True)
    task_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    requested_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    payload_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    decided_by: Mapped[UUID | None] = mapped_column(PG_UUID, ForeignKey("users.id", ondelete="SET NULL"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    task: Mapped[Task] = relationship(back_populates="approvals")


class Verdict(Base):
    __tablename__ = "verdicts"

    task_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    outcome: Mapped[str] = mapped_column(String(30), nullable=False)
    reasons: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False)
    policy_version: Mapped[str] = mapped_column(String(50), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task: Mapped[Task] = relationship(back_populates="verdict")


class LLMCall(Base):
    __tablename__ = "llm_calls"

    id: Mapped[UUID] = mapped_column(PG_UUID, primary_key=True)
    task_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    attempt_id: Mapped[UUID | None] = mapped_column(PG_UUID, ForeignKey("task_attempts.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_usd: Mapped[float] = mapped_column(nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    transcript_artifact_id: Mapped[UUID | None] = mapped_column(PG_UUID, ForeignKey("artifacts.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task: Mapped[Task] = relationship(back_populates="llm_calls")


class PullRequest(Base):
    __tablename__ = "pull_requests"

    task_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    github_pr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    head_branch: Mapped[str] = mapped_column(String(255), nullable=False)
    head_sha: Mapped[str] = mapped_column(CHAR(40), nullable=False)
    base_sha: Mapped[str] = mapped_column(CHAR(40), nullable=False)
    outcome_at_creation: Mapped[str] = mapped_column(String(30), nullable=False)
    draft: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID, ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task: Mapped[Task] = relationship(back_populates="pull_request")


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    user_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    route: Mapped[str] = mapped_column(String(255), primary_key=True)
    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    request_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    response_body: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_user_id: Mapped[UUID | None] = mapped_column(PG_UUID, ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[UUID | None] = mapped_column(PG_UUID)
    metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    ip: Mapped[str | None] = mapped_column(INET)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id: Mapped[UUID] = mapped_column(PG_UUID, primary_key=True)
    github_delivery_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    event: Mapped[str] = mapped_column(String(100), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
