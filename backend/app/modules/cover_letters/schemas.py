import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CoverLetterDraft(BaseModel):
    """A drafted cover letter grounded in the candidate's real CV chunks.

    This is the LLM agent's structured output (PLAN.md §11.1). The DB
    persistence model with the same name lives in
    ``app.modules.cover_letters.models``.
    """

    subject: str = Field(
        description=(
            "Email subject line. Specific to the role and company, not "
            "generic. Format: 'Application: <role> — <candidate name>'"
        )
    )
    body: str = Field(
        description=(
            "Full cover letter body, 250-350 words. Plain text with "
            "paragraph breaks. End with 'Best regards,\\n<name>'. No "
            "salutation block at the very top — the user adds that."
        )
    )
    referenced_cv_chunk_ids: list[uuid.UUID] = Field(
        description=(
            "IDs of CV chunks whose content is referenced or paraphrased "
            "in the body. Used to verify the letter is grounded in real "
            "experience."
        )
    )
    tone: str = Field(
        description=(
            "Short label for the chosen tone: 'plain-direct', "
            "'warm-personal', or 'formal'. Match the tone of the job posting."
        )
    )


class CoverLetterDraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    match_run_id: uuid.UUID | None
    subject: str
    body: str
    referenced_chunks: list[uuid.UUID]
    tone: str | None
    llm_model: str
    created_at: datetime
