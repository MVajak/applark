import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InterviewPrepRun(Base):
    """One run of the interview-prep agent for a specific job.

    The three JSONB columns hold the agent's structured output verbatim:
    ``likely_areas_of_focus`` is a list of short phrases, ``questions`` a
    list of serialised :class:`InterviewQuestion` dicts, and
    ``questions_to_ask_them`` a list of strings.
    """

    __tablename__ = "interview_prep_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        index=True,
    )
    role_overview: Mapped[str] = mapped_column(Text)
    likely_areas_of_focus: Mapped[list[str]] = mapped_column(JSONB)
    questions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    questions_to_ask_them: Mapped[list[str]] = mapped_column(JSONB)
    llm_model: Mapped[str] = mapped_column(Text)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
