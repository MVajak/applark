import uuid
from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.cv.models import CVChunk, CVDocument
from app.modules.cv.schemas import CVDocumentKind


async def add_document(session: AsyncSession, document: CVDocument) -> CVDocument:
    session.add(document)
    await session.flush()
    await session.refresh(document)
    return document


async def get_document(session: AsyncSession, document_id: uuid.UUID) -> CVDocument | None:
    return await session.get(CVDocument, document_id)


async def get_document_with_chunks(
    session: AsyncSession, user_id: uuid.UUID, document_id: uuid.UUID
) -> CVDocument | None:
    stmt = (
        select(CVDocument)
        .where(CVDocument.id == document_id, CVDocument.user_id == user_id)
        .options(selectinload(CVDocument.chunks))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_documents(
    session: AsyncSession,
    *,
    kind: CVDocumentKind | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[CVDocument]:
    stmt = select(CVDocument).order_by(CVDocument.created_at.desc()).limit(limit).offset(offset)
    if kind is not None:
        stmt = stmt.where(CVDocument.kind == kind)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_latest_document_with_chunks(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    kind: CVDocumentKind | None = None,
) -> CVDocument | None:
    """Return the user's most recently uploaded document (with chunks loaded)."""
    stmt = (
        select(CVDocument)
        .where(CVDocument.user_id == user_id)
        .options(selectinload(CVDocument.chunks))
        .order_by(CVDocument.created_at.desc())
        .limit(1)
    )
    if kind is not None:
        stmt = stmt.where(CVDocument.kind == kind)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_documents_with_chunks(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    kind: CVDocumentKind | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[CVDocument]:
    stmt = (
        select(CVDocument)
        .where(CVDocument.user_id == user_id)
        .options(selectinload(CVDocument.chunks))
        .order_by(CVDocument.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if kind is not None:
        stmt = stmt.where(CVDocument.kind == kind)
    result = await session.execute(stmt)
    return result.scalars().all()


async def delete_document(
    session: AsyncSession, user_id: uuid.UUID, document_id: uuid.UUID
) -> bool:
    document = await session.get(CVDocument, document_id)
    if document is None or document.user_id != user_id:
        return False
    await session.delete(document)
    return True


async def add_chunks(session: AsyncSession, chunks: Sequence[CVChunk]) -> Sequence[CVChunk]:
    session.add_all(chunks)
    await session.flush()
    return chunks


async def list_chunks_by_document(
    session: AsyncSession, document_id: uuid.UUID
) -> Sequence[CVChunk]:
    stmt = (
        select(CVChunk)
        .where(CVChunk.document_id == document_id)
        .order_by(CVChunk.chunk_index.asc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def delete_chunks_by_document(session: AsyncSession, document_id: uuid.UUID) -> int:
    """Hard-delete all chunks for a document. Used for retry idempotency."""
    result = await session.execute(delete(CVChunk).where(CVChunk.document_id == document_id))
    return int(result.rowcount)  # pyright: ignore  # CursorResult.rowcount exists at runtime
