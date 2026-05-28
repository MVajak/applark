import uuid
from typing import Any

import structlog
from redis.asyncio import Redis

from app.core.database import SessionLocal
from app.core.events import EVENTS_CV, publish
from app.modules.cv import service as cv_service
from app.modules.cv.events import CvProcessingEvent

logger = structlog.get_logger(__name__)


async def chunk_and_embed_cv(ctx: dict[str, Any], document_id: str) -> dict[str, Any]:
    """ARQ task: chunk a CV via the agent and embed each chunk.

    Idempotent on retry: any existing chunks for the document are deleted
    before reprocessing.
    """
    doc_id = uuid.UUID(document_id)
    logger.info(
        "chunk_and_embed_cv_start",
        document_id=str(doc_id),
        job_try=ctx.get("job_try"),
    )

    async with SessionLocal() as session:
        deleted, created = await cv_service.reprocess_cv_document(session, doc_id)
        await session.commit()

    logger.info(
        "chunk_and_embed_cv_done",
        document_id=str(doc_id),
        deleted_chunks=deleted,
        created_chunks=created,
    )

    redis = ctx.get("redis")
    if isinstance(redis, Redis):
        await publish(
            redis,
            EVENTS_CV,
            CvProcessingEvent(document_id=doc_id, chunks_ready=True),
        )

    return {"document_id": str(doc_id), "created_chunks": created}
