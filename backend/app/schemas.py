from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class JobCreate(BaseModel):
    domain: str = Field(..., min_length=1)

class JobResponse(BaseModel):
    job_id: str
    status: str

class JobListItem(BaseModel):
    id: UUID
    domain: str
    status: str
    attempts: int
    result_count: int | None
    created_at: datetime
    finished_at: datetime | None

    class Config:
        from_attributes = True

class ReviewUpdate(BaseModel):
    reviewed: bool
