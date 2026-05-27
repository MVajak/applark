import uuid
from collections.abc import Sequence

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.embeddings import get_embeddings
from app.modules.cv import repository
from app.modules.cv.agent import cv_extractor
from app.modules.cv.models import CVChunk
from app.modules.cv.schemas import CVChunkType, CVExtraction, ExtractedCVChunk

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

    user_message = (
        f"<cv>\n{raw_text}\n</cv>\n\n"
        "Extract structured chunks per the rules above."
    )
    result = await cv_extractor.run(user_message)
    usage = result.usage()
    logger.info(
        "cv_extraction_done",
        input_tokens=getattr(usage, "input_tokens", None)
        or getattr(usage, "request_tokens", None),
        output_tokens=getattr(usage, "output_tokens", None)
        or getattr(usage, "response_tokens", None),
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
    has_language_chunk = any(
        c.chunk_type == CVChunkType.language for c in extraction.chunks
    )
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
