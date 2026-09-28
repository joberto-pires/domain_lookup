from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Job, HostnameReview
from app.schemas import JobCreate, JobResponse, JobListItem, ReviewUpdate
from app.normalization import normalize_domain
from app.worker import lookup_domain
from app.config import settings

router = APIRouter()

@router.post("/jobs", status_code=202)
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    try:
        domain = normalize_domain(payload.domain)
    except ValueError:
        raise HTTPException(422, "Invalid domain")

    existing = (
        db.query(Job)
        .filter(Job.domain == domain, Job.status.in_(("queued", "running", "retrying")))
        .first()
    )
    if existing:
        return {"job_id": str(existing.id), "status": existing.status}

    job = Job(domain=domain, status="queued", max_attempts=settings.max_attempts)
    db.add(job)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(Job)
            .filter(Job.domain == domain, Job.status.in_(("queued", "running", "retrying")))
            .first()
        )
        return {"job_id": str(existing.id), "status": existing.status}

    lookup_domain.delay(str(job.id))
    return {"job_id": str(job.id), "status": "queued"}

@router.get("/jobs")
def list_jobs(
    domain: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    q = db.query(Job)
    if domain:
        q = q.filter(Job.domain == normalize_domain(domain))
    if status_filter:
        q = q.filter(Job.status == status_filter)
    jobs = q.order_by(Job.created_at.desc()).offset(offset).limit(limit).all()
    return [JobListItem.model_validate(j) for j in jobs]

@router.get("/jobs/{job_id}")
def get_job(job_id: UUID, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    reviews = {
        r.hostname: r.reviewed
        for r in db.query(HostnameReview).filter(HostnameReview.domain == job.domain).all()
    }

    results = []
    for r in job.results:
        results.append({"hostname": r.hostname, "reviewed": reviews.get(r.hostname, False)})

    changes = {"added": [], "removed": [], "unchanged": []}
    for c in job.changes:
        changes[c.kind].append({"hostname": c.hostname, "reviewed": reviews.get(c.hostname, False)})

    return {
        "id": str(job.id),
        "domain": job.domain,
        "status": job.status,
        "attempts": job.attempts,
        "error": job.error,
        "result_count": job.result_count,
        "previous_success_job_id": str(job.previous_success_job_id) if job.previous_success_job_id else None,
        "added_count": job.added_count,
        "removed_count": job.removed_count,
        "unchanged_count": job.unchanged_count,
        "results": results,
        "changes": changes,
        "created_at": job.created_at,
        "finished_at": job.finished_at,
    }

@router.put("/domains/{domain}/hostnames/{hostname}/review")
def set_review(domain: str, hostname: str, payload: ReviewUpdate, db: Session = Depends(get_db)):
    domain = normalize_domain(domain)
    review = (
        db.query(HostnameReview)
        .filter(HostnameReview.domain == domain, HostnameReview.hostname == hostname)
        .first()
    )
    if review:
        review.reviewed = payload.reviewed
    else:
        db.add(HostnameReview(domain=domain, hostname=hostname, reviewed=payload.reviewed))
    db.commit()
    return {"domain": domain, "hostname": hostname, "reviewed": payload.reviewed}
