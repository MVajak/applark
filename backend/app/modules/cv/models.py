import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector  # pyright: ignore[reportMissingTypeStubs]
from sqlalchemy import Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.cv.schemas import CVChunkType, CVDocumentKind


class CVDocument(Base):
    __tablename__ = "cv_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    kind: Mapped[CVDocumentKind] = mapped_column(
        Enum(CVDocumentKind, name="cv_document_kind", create_type=False),
    )
    filename: Mapped[str] = mapped_column(String)
    candidate_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_text: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    chunks: Mapped[list["CVChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="CVChunk.chunk_index",
    )


class CVChunk(Base):
    __tablename__ = "cv_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cv_documents.id", ondelete="CASCADE"),
        index=True,
    )
    chunk_type: Mapped[CVChunkType] = mapped_column(
        Enum(CVChunkType, name="cv_chunk_type", create_type=False),
    )
    content: Mapped[str] = mapped_column(String)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        server_default="{}",
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    document: Mapped[CVDocument] = relationship(back_populates="chunks")
