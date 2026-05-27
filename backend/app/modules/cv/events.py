"""SSE event payload for CV processing completion."""

import uuid

from pydantic import BaseModel


class CvProcessingEvent(BaseModel):
    document_id: uuid.UUID
    chunks_ready: bool
