"""Celery application for workflow execution."""

from celery import Celery
from celery.schedules import crontab

from hivecode.config import get_settings

settings = get_settings()

celery_app = Celery(
    "hivecode",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["hivecode.worker.tasks"],
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    worker_concurrency=1,
    task_time_limit=settings.task_time_limit_s + 300,  # Hard limit + grace
    task_soft_time_limit=settings.task_time_limit_s,
    broker_connection_retry_on_startup=True,
    result_expires=3600,
)

# Beat schedule — sweeper runs every minute
celery_app.conf.beat_schedule = {
    "sweeper-recovery": {
        "task": "hivecode.worker.sweeper.recover_orphaned_tasks",
        "schedule": crontab(minute="*"),
    },
    "sweeper-expire-approvals": {
        "task": "hivecode.worker.sweeper.expire_approvals",
        "schedule": crontab(minute="*/5"),
    },
    "sweeper-reap-artifacts": {
        "task": "hivecode.worker.sweeper.reap_expired_artifacts",
        "schedule": crontab(minute="*/15"),
    },
}
