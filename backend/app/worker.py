import logging
from datetime import datetime, timezone
from celery.exceptions import MaxRetriesExceededError
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Job, JobAttempt, JobResult, JobChange
from app.normalization import normalize_hostnames
from app.provider import fetch_hostnames, ProviderError
from app.config import settings

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=2, acks_late=True)
def lookup_domain(self, job_id: str):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).with_for_update().first()
        if job is None:
            return
        if job.status == "succeeded":
            db.close()
            return  # safe replay: do not fetch again

        attempt_number = job.attempts + 1
        job.attempts = attempt_number
        job.status = "running"
        job.started_at = job.started_at or datetime.now(timezone.utc)

        attempt = JobAttempt(
            job_id=job.id,
            attempt_number=attempt_number,
            status="running",
        )
        db.add(attempt)
        db.commit()

        try:
            raw_hostnames = fetch_hostnames(job.domain)
        except ProviderError as exc:
            _handle_provider_error(db, job, attempt, exc, self)
            return

        hostnames = normalize_hostnames(raw_hostnames)
        _commit_success(db, job, attempt, hostnames)

    finally:
        db.close()

def _handle_provider_error(db, job, attempt, exc, task):
    attempt.status = "failed"
    attempt.error = str(exc)
    attempt.http_status = exc.http_status
    attempt.finished_at = datetime.now(timezone.utc)

    if exc.retryable and job.attempts < job.max_attempts:
        job.status = "retrying"
        job.error = str(exc)
        db.commit()
        try:
            task.retry(countdown=settings.retry_delay_seconds, exc=exc)
        except MaxRetriesExceededError:
            _fail_job(db, job, str(exc))
    else:
        _fail_job(db, job, str(exc))

def _fail_job(db, job, error):
    job.status = "failed"
    job.error = error
    job.finished_at = datetime.now(timezone.utc)
    db.commit()

def _commit_success(db, job, attempt, hostnames):
    previous = (
        db.query(Job)
        .filter(Job.domain == job.domain, Job.status == "succeeded", Job.id != job.id)
        .order_by(Job.finished_at.desc())
        .first()
    )

    current_set = set(hostnames)
    if previous:
        prev_hostnames = {r.hostname for r in previous.results}
        added = current_set - prev_hostnames
        removed = prev_hostnames - current_set
        unchanged = current_set & prev_hostnames
        job.previous_success_job_id = previous.id
    else:
        added, removed, unchanged = set(), set(), set()

    job.status = "succeeded"
    job.result_count = len(hostnames)
    job.added_count = len(added)
    job.removed_count = len(removed)
    job.unchanged_count = len(unchanged)
    job.error = None
    job.finished_at = datetime.now(timezone.utc)
    attempt.status = "succeeded"
    attempt.finished_at = datetime.now(timezone.utc)

    for hostname in hostnames:
        db.add(JobResult(job_id=job.id, hostname=hostname))
    for hostname in added:
        db.add(JobChange(job_id=job.id, kind="added", hostname=hostname))
    for hostname in removed:
        db.add(JobChange(job_id=job.id, kind="removed", hostname=hostname))
    for hostname in unchanged:
        db.add(JobChange(job_id=job.id, kind="unchanged", hostname=hostname))

    db.commit()
