"""Sweeper — scheduled recovery and cleanup tasks."""

from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy import select

from hivecode.db.base import async_session_factory
from hivecode.db.models import Approval, Artifact, Task


@shared_task
def recover_orphaned_tasks():
    """Re-enqueue non-terminal tasks whose lease has expired.

    Runs every minute via Celery beat.
    """
    # TODO: Implement recovery logic
    # 1. Find tasks in 'running' state with expired lease
    # 2. Re-enqueue them via Celery
    pass


@shared_task
def expire_approvals():
    """Expire pending approvals past their expiry time.

    Runs every 5 minutes via Celery beat.
    """
    # TODO: Implement approval expiry
    pass


@shared_task
def reap_expired_artifacts():
    """Delete expired artifacts from object storage.

    Runs every 15 minutes via Celery beat.
    """
    # TODO: Implement artifact reaping
    pass
