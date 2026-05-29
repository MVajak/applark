import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CVTailorRun(Base):
    """A run of the CV tailor agent against a specific job.

    ``suggestions`` stores a list of serialised :class:`TailorSuggestion`
    dicts; ``do_not_suggest`` stores a plain list of sentence strings.
    Both are kept as JSONB so we can re-validate them through Pydantic on
    read without a separate join table.
    """

    __tablename__ = "cv_tailor_runs"

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
    job_summary: Mapped[str] = mapped_column(Text)
    suggestions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    do_not_suggest: Mapped[list[str]] = mapped_column(JSONB)
    llm_model: Mapped[str] = mapped_column(Text)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
