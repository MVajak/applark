"""SSE event payload for job status transitions."""

import uuid

from pydantic import BaseModel

from app.modules.jobs.schemas import JobStatus


class JobStatusEvent(BaseModel):
    job_id: uuid.UUID
    status: JobStatus
    error_message: str | None = None
