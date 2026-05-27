import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class QuestionCategory(StrEnum):
    technical = "technical"
    behavioral = "behavioral"
    system_design = "system_design"
    role_specific = "role_specific"
    culture_fit = "culture_fit"


class InterviewQuestion(BaseModel):
    category: QuestionCategory
    question: str = Field(description="The full question as the interviewer would ask it")
    why_likely: str = Field(
        description=(
            "One sentence: why this question is likely for THIS specific role. "
            "Reference a requirement, tech stack item, or company trait."
        )
    )
    suggested_angle: str = Field(
        description=(
            "How the candidate should approach answering. Reference specific "
            "CV chunks where they have relevant experience to draw on."
        )
    )
    referenced_cv_chunk_ids: list[uuid.UUID] = Field(
        description=(
            "CV chunks the candidate can draw on. May be empty if they lack "
            "direct experience for this question."
        )
    )


class InterviewPrepResult(BaseModel):
    role_overview: str = Field(
        description="2-3 sentence summary of what to expect from this interview"
    )
    likely_areas_of_focus: list[str] = Field(
        description="3-5 short phrases naming what they'll probably probe"
    )
    questions: list[InterviewQuestion] = Field(
        description="8-12 questions distributed across categories"
    )
    questions_to_ask_them: list[str] = Field(
        description=(
            "3-5 thoughtful questions the candidate should ask the interviewer. "
            "Specific to this company/role, not generic."
        )
    )


class InterviewPrepRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    role_overview: str
    likely_areas_of_focus: list[str]
    questions: list[InterviewQuestion]
    questions_to_ask_them: list[str]
    llm_model: str
    created_at: datetime
