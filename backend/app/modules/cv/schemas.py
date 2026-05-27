import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CVDocumentKind(StrEnum):
    cv = "cv"
    cover_letter = "cover_letter"


class CVChunkType(StrEnum):
    summary = "summary"
    experience = "experience"
    skill = "skill"
    education = "education"
    project = "project"
    language = "language"
    other = "other"


class ExtractedCVChunk(BaseModel):
    chunk_type: CVChunkType = Field(
        description=(
            "Which kind of CV section this chunk represents. Use 'other' only "
            "when nothing else fits."
        )
    )
    content: str = Field(
        description=(
            "The candidate's exact wording for this chunk. Quote the CV "
            "verbatim — paraphrasing loses the specific terminology that "
            "drives good matches against job requirements."
        )
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Structured details about this chunk. For 'experience': company, "
            "role, start_date, end_date. For 'education': institution, "
            "degree, year. For 'project': name, technologies (list of "
            "lowercase strings). Empty object for chunks without structured "
            "details."
        ),
    )


class CVExtraction(BaseModel):
    candidate_name: str = Field(description="The candidate's full name as written on the CV.")
    languages_spoken: list[str] = Field(
        default_factory=list,
        description=(
            "Spoken languages mentioned anywhere on the CV. Lowercase. "
            "Deduplicated. Empty list if not mentioned."
        ),
    )
    chunks: list[ExtractedCVChunk] = Field(
        description=(
            "One chunk per real-world entry. Do not split a single role "
            "into multiple chunks by bullet point — keep all responsibilities "
            "and achievements for one role together in one experience chunk."
        )
    )


class CVChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    chunk_type: CVChunkType
    content: str
    metadata: dict[str, Any] = Field(validation_alias="metadata_")
    chunk_index: int
    embedding_model: str | None
    created_at: datetime


class CVDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: CVDocumentKind
    filename: str
    candidate_name: str | None
    raw_text: str
    chunks: list[CVChunkRead]
    created_at: datetime
    updated_at: datetime
