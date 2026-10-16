"""Repository layer — all database access goes through these functions."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from hivecode.db.models import (
    Approval,
    Artifact,
    CheckRun,
    LLMCall,
    PullRequest,
    Repository,
    ReviewFinding,
    Task,
    TaskAttempt,
    TaskEvent,
    User,
    UserRepositoryGrant,
    Verdict,
)


class TaskRepository:
    """Repository for Task entities."""

    @staticmethod
    async def get_by_id(db: AsyncSession, task_id: UUID, user_id: UUID) -> Task | None:
        """Get a task by ID, scoped to the owning user. Returns None if not found or not owned."""
        result = await db.execute(
            select(Task)
            .where(Task.id == task_id, Task.user_id == user_id)
            .options(
                selectinload(Task.repository),
                selectinload(Task.attempts),
                selectinload(Task.verdict),
                selectinload(Task.pull_request),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_user(
        db: AsyncSession,
        user_id: UUID,
        *,
        repository_id: UUID | None = None,
        outcome: str | None = None,
        cursor: str | None = None,
        limit: int = 20,
    ) -> list[Task]:
        """List tasks for a user with optional filtering and cursor pagination."""
        stmt = (
            select(Task)
            .where(Task.user_id == user_id)
            .order_by(Task.created_at.desc())
            .limit(limit + 1)
        )

        if repository_id:
            stmt = stmt.where(Task.repository_id == repository_id)
        if outcome:
            stmt = stmt.where(Task.outcome == outcome)
        if cursor:
            from datetime import datetime

            cursor_dt = datetime.fromisoformat(cursor)
            stmt = stmt.where(Task.created_at < cursor_dt)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create(db: AsyncSession, task: Task) -> Task:
        """Insert a new task."""
        db.add(task)
        await db.flush()
        return task

    @staticmethod
    async def update_state(
        db: AsyncSession,
        task_id: UUID,
        *,
        state: str | None = None,
        stage: str | None = None,
        outcome: str | None = None,
        version: int = 0,
    ) -> Task | None:
        """Update task state with optimistic concurrency."""
        task = await db.get(Task, task_id)
        if task is None or task.version != version:
            return None

        if state is not None:
            task.state = state
        if stage is not None:
            task.stage = stage
        if outcome is not None:
            task.outcome = outcome
        task.version += 1
        await db.flush()
        return task


class TaskAttemptRepository:
    """Repository for TaskAttempt entities."""

    @staticmethod
    async def get_by_id(db: AsyncSession, attempt_id: UUID) -> TaskAttempt | None:
        result = await db.execute(
            select(TaskAttempt)
            .where(TaskAttempt.id == attempt_id)
            .options(selectinload(TaskAttempt.check_runs))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_task(db: AsyncSession, task_id: UUID) -> list[TaskAttempt]:
        result = await db.execute(
            select(TaskAttempt)
            .where(TaskAttempt.task_id == task_id)
            .order_by(TaskAttempt.attempt_no)
            .options(selectinload(TaskAttempt.check_runs))
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(db: AsyncSession, attempt: TaskAttempt) -> TaskAttempt:
        db.add(attempt)
        await db.flush()
        return attempt


class CheckRunRepository:
    """Repository for CheckRun entities."""

    @staticmethod
    async def list_by_attempt(db: AsyncSession, attempt_id: UUID) -> list[CheckRun]:
        result = await db.execute(
            select(CheckRun)
            .where(CheckRun.attempt_id == attempt_id)
            .order_by(CheckRun.check_key, CheckRun.run_seq)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_by_task(db: AsyncSession, task_id: UUID) -> list[CheckRun]:
        result = await db.execute(
            select(CheckRun)
            .where(CheckRun.task_id == task_id)
            .order_by(CheckRun.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(db: AsyncSession, check_run: CheckRun) -> CheckRun:
        db.add(check_run)
        await db.flush()
        return check_run


class TaskEventRepository:
    """Repository for TaskEvent entities."""

    @staticmethod
    async def get_events_after(
        db: AsyncSession, task_id: UUID, after_seq: int, limit: int = 100
    ) -> list[TaskEvent]:
        result = await db.execute(
            select(TaskEvent)
            .where(TaskEvent.task_id == task_id, TaskEvent.seq > after_seq)
            .order_by(TaskEvent.seq)
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_latest_seq(db: AsyncSession, task_id: UUID) -> int:
        result = await db.execute(
            select(TaskEvent.seq)
            .where(TaskEvent.task_id == task_id)
            .order_by(TaskEvent.seq.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return row if row is not None else 0

    @staticmethod
    async def append(db: AsyncSession, event: TaskEvent) -> TaskEvent:
        """Append an event with gapless sequence assignment."""
        latest = await TaskEventRepository.get_latest_seq(db, event.task_id)
        event.seq = latest + 1
        db.add(event)
        await db.flush()
        return event


class RepositoryRepository:
    """Repository for Repository entities."""

    @staticmethod
    async def list_by_user(db: AsyncSession, user_id: UUID) -> list[Repository]:
        """List repositories accessible to the user via grants."""
        result = await db.execute(
            select(Repository)
            .join(UserRepositoryGrant, UserRepositoryGrant.repository_id == Repository.id)
            .where(UserRepositoryGrant.user_id == user_id)
            .order_by(Repository.full_name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, repo_id: UUID) -> Repository | None:
        result = await db.execute(select(Repository).where(Repository.id == repo_id))
        return result.scalar_one_or_none()


class UserRepository:
    """Repository for User entities."""

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: UUID) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_github_id(db: AsyncSession, github_user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.github_user_id == github_user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user: User) -> User:
        db.add(user)
        await db.flush()
        return user


class ArtifactRepository:
    """Repository for Artifact entities."""

    @staticmethod
    async def create(db: AsyncSession, artifact: Artifact) -> Artifact:
        db.add(artifact)
        await db.flush()
        return artifact

    @staticmethod
    async def get_by_id(db: AsyncSession, artifact_id: UUID) -> Artifact | None:
        result = await db.execute(select(Artifact).where(Artifact.id == artifact_id))
        return result.scalar_one_or_none()


class ReviewFindingRepository:
    """Repository for ReviewFinding entities."""

    @staticmethod
    async def list_by_task(db: AsyncSession, task_id: UUID) -> list[ReviewFinding]:
        result = await db.execute(
            select(ReviewFinding)
            .where(ReviewFinding.task_id == task_id)
            .order_by(ReviewFinding.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(db: AsyncSession, finding: ReviewFinding) -> ReviewFinding:
        db.add(finding)
        await db.flush()
        return finding


class ApprovalRepository:
    """Repository for Approval entities."""

    @staticmethod
    async def get_by_id(db: AsyncSession, approval_id: UUID) -> Approval | None:
        result = await db.execute(select(Approval).where(Approval.id == approval_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_pending_by_task(db: AsyncSession, task_id: UUID) -> list[Approval]:
        result = await db.execute(
            select(Approval)
            .where(Approval.task_id == task_id, Approval.status == "pending")
            .order_by(Approval.requested_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(db: AsyncSession, approval: Approval) -> Approval:
        db.add(approval)
        await db.flush()
        return approval


class VerdictRepository:
    """Repository for Verdict entities."""

    @staticmethod
    async def get_by_task_id(db: AsyncSession, task_id: UUID) -> Verdict | None:
        result = await db.execute(select(Verdict).where(Verdict.task_id == task_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, verdict: Verdict) -> Verdict:
        db.add(verdict)
        await db.flush()
        return verdict


class LLMCallRepository:
    """Repository for LLMCall entities."""

    @staticmethod
    async def create(db: AsyncSession, call: LLMCall) -> LLMCall:
        db.add(call)
        await db.flush()
        return call


class PullRequestRepository:
    """Repository for PullRequest entities."""

    @staticmethod
    async def get_by_task_id(db: AsyncSession, task_id: UUID) -> PullRequest | None:
        result = await db.execute(select(PullRequest).where(PullRequest.task_id == task_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, pr: PullRequest) -> PullRequest:
        db.add(pr)
        await db.flush()
        return pr
