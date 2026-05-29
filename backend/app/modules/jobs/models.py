import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector  # pyright: ignore[reportMissingTypeStubs]
from sqlalchemy import Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.jobs.schemas import (
    JobSourceKind,
    JobStatus,
    RemotePolicy,
    RequirementCategory,
    Seniority,
)


class Job(Base):
    __tablename__ = "jobs"

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
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    source_kind: Mapped[JobSourceKind] = mapped_column(
        Enum(JobSourceKind, name="job_source_kind", create_type=False),
    )
    raw_text: Mapped[str] = mapped_column(String)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status", create_type=False),
        server_default="pending",
    )
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    company: Mapped[str | None] = mapped_column(String, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    remote_policy: Mapped[RemotePolicy] = mapped_column(
        Enum(RemotePolicy, name="remote_policy", create_type=False),
        server_default="unspecified",
    )
    seniority: Mapped[Seniority] = mapped_column(
        Enum(Seniority, name="seniority", create_type=False),
        server_default="unspecified",
    )
    tech_stack: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        server_default="{}",
    )
    salary_range: Mapped[str | None] = mapped_column(String, nullable=True)
    summary: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_extraction: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    requirements: Mapped[list["JobRequirement"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="JobRequirement.created_at",
    )


class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
    )
    text: Mapped[str] = mapped_column(String)
    category: Mapped[RequirementCategory] = mapped_column(
        Enum(RequirementCategory, name="requirement_category", create_type=False),
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    job: Mapped[Job] = relationship(back_populates="requirements")
