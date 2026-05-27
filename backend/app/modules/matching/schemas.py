import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MappedExperience(BaseModel):
    requirement_text: str = Field(
        description="The job requirement being matched, quoted from the posting"
    )
    cv_chunk_id: uuid.UUID
    cv_chunk_excerpt: str = Field(
        description="The candidate's actual wording, quoted from their CV"
    )
    why_it_matches: str = Field(
        description="One specific sentence, no generic claims"
    )


class Gap(BaseModel):
    requirement_text: str
    severity: float = Field(
        ge=0,
        le=1,
        description="0-1. Required gaps near 1.0, nice-to-have gaps lower",
    )


class MatchExplanation(BaseModel):
    overall_score: float = Field(
        ge=0,
        le=1,
        description="Honest fit score. 0.4 for partial match, not 0.8",
    )
    summary: str = Field(description="2-3 sentences. Direct, no marketing fluff")
    strengths: list[MappedExperience]
    gaps: list[Gap]
    suggested_emphasis: list[str] = Field(
        description="3-5 experiences to lead with in a cover letter"
    )


class MatchRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    overall_score: float
    summary: str
    details: MatchExplanation
    llm_model: str
    created_at: datetime
