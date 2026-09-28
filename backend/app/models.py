import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, TIMESTAMP,
    ForeignKey, UniqueConstraint, Index, Float
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

ACTIVE_STATUSES = ("queued", "running", "retrying")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="queued")
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    error = Column(Text, nullable=True)
    result_count = Column(Integer, nullable=True)
    previous_success_job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    added_count = Column(Integer, nullable=True)
    removed_count = Column(Integer, nullable=True)
    unchanged_count = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    finished_at = Column(TIMESTAMP(timezone=True), nullable=True)

    attempts_rel = relationship("JobAttempt", back_populates="job", cascade="all, delete-orphan")
    results = relationship("JobResult", back_populates="job", cascade="all, delete-orphan")
    changes = relationship("JobChange", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index(
            "one_active_job_per_domain",
            "domain",
            unique=True,
            postgresql_where=Column("status").in_(ACTIVE_STATUSES),
        ),
    )

class JobAttempt(Base):
    __tablename__ = "job_attempts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    status = Column(String, nullable=False)  # running, retrying, failed, succeeded
    error = Column(Text, nullable=True)
    http_status = Column(Integer, nullable=True)
    started_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    finished_at = Column(TIMESTAMP(timezone=True), nullable=True)
    job = relationship("Job", back_populates="attempts_rel")

class JobResult(Base):
    __tablename__ = "job_results"
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), primary_key=True)
    hostname = Column(String, primary_key=True)
    job = relationship("Job", back_populates="results")

class JobChange(Base):
    __tablename__ = "job_changes"
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), primary_key=True)
    kind = Column(String, primary_key=True)  # added, removed, unchanged
    hostname = Column(String, primary_key=True)
    job = relationship("Job", back_populates="changes")

class HostnameReview(Base):
    __tablename__ = "hostname_reviews"
    domain = Column(String, primary_key=True)
    hostname = Column(String, primary_key=True)
    reviewed = Column(Boolean, nullable=False, default=False)
    updated_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
