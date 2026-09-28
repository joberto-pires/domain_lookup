from celery import Celery
from app.config import settings

celery_app = Celery(
    "domain_lookup",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=settings.retry_delay_seconds,
    broker_connection_retry_on_startup=True,
)

celery_app.autodiscover_tasks(["app"])
