import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class SuggestionKind(StrEnum):
    emphasize = "emphasize"
    rephrase = "rephrase"
    add_detail = "add_detail"
    deprioritize = "deprioritize"


class TailorSuggestion(BaseModel):
    kind: SuggestionKind
    cv_chunk_id: uuid.UUID = Field(description="The existing CV chunk this suggestion applies to")
    rationale: str = Field(
        description=(
            "One sentence: why this change helps for THIS specific job. "
            "Reference the job requirement or tech stack item that drove it."
        )
    )
    suggested_text: str | None = Field(
        description=(
            "For 'rephrase' or 'add_detail' suggestions, the proposed new "
            "wording. Null for emphasize/deprioritize."
        )
    )


class CVTailorResult(BaseModel):
    job_summary: str = Field(description="One sentence framing what this job most cares about")
    suggestions: list[TailorSuggestion] = Field(
        description="3-7 specific, actionable suggestions. Quality over quantity."
    )
    do_not_suggest: list[str] = Field(
        description=(
            "Things the candidate should NOT add even if tempting — claims "
            "that would overstate fit. Each item is one sentence."
        )
    )


class CVTailorRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    job_summary: str
    suggestions: list[TailorSuggestion]
    do_not_suggest: list[str]
    llm_model: str
    created_at: datetime
