import uuid
from collections.abc import Sequence

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.embeddings import get_embeddings
from app.core.llm import extract_token_usage
from app.modules.cv import repository
from app.modules.cv.agent import cv_extractor
from app.modules.cv.models import CVChunk, CVDocument
from app.modules.cv.parser import extract_text_from_pdf
from app.modules.cv.schemas import (
    CVChunkType,
    CVDocumentKind,
    CVExtraction,
    ExtractedCVChunk,
)

logger = structlog.get_logger(__name__)

# Hard cap so a pathologically long CV (or a scraped PDF with extracted noise)
# can't blow up our per-call Anthropic cost.
MAX_RAW_TEXT_CHARS = 20_000


async def run_cv_extraction(raw_text: str) -> CVExtraction:
    """Run the CV chunker agent on raw text and log usage."""
    if len(raw_text) > MAX_RAW_TEXT_CHARS:
        logger.warning(
            "cv_raw_text_truncated",
            original_chars=len(raw_text),
            truncated_to=MAX_RAW_TEXT_CHARS,
        )
        raw_text = raw_text[:MAX_RAW_TEXT_CHARS]

    user_message = f"<cv>\n{raw_text}\n</cv>\n\nExtract structured chunks per the rules above."
    result = await cv_extractor.run(user_message)
    input_tokens, output_tokens = extract_token_usage(result.usage())
    logger.info(
        "cv_extraction_done",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        chunks=len(result.output.chunks),
        candidate_name=result.output.candidate_name,
    )
    return result.output


async def persist_cv_chunks(
    session: AsyncSession,
    document_id: uuid.UUID,
    extraction: CVExtraction,
) -> Sequence[CVChunk]:
    """Compute embeddings per chunk and persist as CVChunk rows.

    All chunk embeddings are fetched in a single batched OpenAI call.
    Caller owns the transaction.
    """
    # The agent puts spoken languages on a top-level CVExtraction field and
    # the prompt rules don't ask for a 'language' chunk explicitly, so the
    # chunker rarely produces one. Without it, the matcher's vector search
    # has nothing to map to a "Proficiency in Estonian/English" requirement.
    # Synthesise one if absent.
    languages = [lang.lower() for lang in extraction.languages_spoken]
    has_language_chunk = any(c.chunk_type == CVChunkType.language for c in extraction.chunks)
    if languages and not has_language_chunk:
        extraction.chunks.append(
            ExtractedCVChunk(
                chunk_type=CVChunkType.language,
                content="Spoken languages: " + ", ".join(languages),
                metadata={"languages": languages},
            )
        )

    if not extraction.chunks:
        return []
    embeddings = await get_embeddings([c.content for c in extraction.chunks])
    chunks: list[CVChunk] = [
        CVChunk(
            document_id=document_id,
            chunk_type=extracted.chunk_type,
            content=extracted.content,
            metadata_=extracted.metadata,
            chunk_index=index,
            embedding=embedding,
            embedding_model=settings.EMBEDDING_MODEL,
        )
        for index, (extracted, embedding) in enumerate(
            zip(extraction.chunks, embeddings, strict=True)
        )
    ]
    return await repository.add_chunks(session, chunks)


# ----- Document CRUD (router-facing; caller owns the transaction) -----


async def create_cv_document(
    session: AsyncSession,
    *,
    file_bytes: bytes,
    filename: str | None,
    kind: CVDocumentKind,
) -> CVDocument:
    """Parse the uploaded PDF and persist a new CVDocument (no commit)."""
    raw_text = extract_text_from_pdf(file_bytes)
    document = CVDocument(kind=kind, filename=filename or "unnamed.pdf", raw_text=raw_text)
    return await repository.add_document(session, document)


async def list_documents(
    session: AsyncSession,
    *,
    kind: CVDocumentKind | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[CVDocument]:
    return await repository.list_documents_with_chunks(
        session, kind=kind, limit=limit, offset=offset
    )


async def get_document_with_chunks(
    session: AsyncSession, document_id: uuid.UUID
) -> CVDocument | None:
    return await repository.get_document_with_chunks(session, document_id)


async def delete_document(session: AsyncSession, document_id: uuid.UUID) -> bool:
    return await repository.delete_document(session, document_id)


async def get_latest_document_with_chunks(
    session: AsyncSession,
    *,
    kind: CVDocumentKind | None = None,
) -> CVDocument | None:
    """Cross-module read backing :class:`~app.modules.cv.protocols.CVProvider`."""
    return await repository.get_latest_document_with_chunks(session, kind=kind)


async def reprocess_cv_document(session: AsyncSession, document_id: uuid.UUID) -> tuple[int, int]:
    """Re-chunk + re-embed a document. Returns (deleted, created). Caller commits.

    Idempotent on retry: any existing chunks are deleted before reprocessing.
    """
    document = await repository.get_document(session, document_id)
    if document is None:
        raise RuntimeError(f"CV document {document_id} not found")

    deleted = await repository.delete_chunks_by_document(session, document_id)
    extraction = await run_cv_extraction(document.raw_text)
    document.candidate_name = extraction.candidate_name
    chunks = await persist_cv_chunks(session, document_id, extraction)
    return deleted, len(chunks)
