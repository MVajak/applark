import uuid
from typing import Annotated

from arq import ArqRedis
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from redis.asyncio import Redis

from app.core.database import SessionLocal
from app.core.events import EVENTS_CV, sse_response
from app.core.redis import get_arq_pool, get_redis
from app.modules.cv import repository
from app.modules.cv.models import CVDocument
from app.modules.cv.parser import extract_text_from_pdf
from app.modules.cv.schemas import CVDocumentKind, CVDocumentRead

router = APIRouter(prefix="/cv", tags=["cv"])


@router.post(
    "/documents",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=CVDocumentRead,
)
async def create_cv_document(
    file: Annotated[UploadFile, File()],
    kind: Annotated[CVDocumentKind, Form()],
    arq_pool: Annotated[ArqRedis, Depends(get_arq_pool)],
) -> CVDocumentRead:
    pdf_bytes = await file.read()
    raw_text = extract_text_from_pdf(pdf_bytes)

    async with SessionLocal() as session:
        document = CVDocument(
            kind=kind,
            filename=file.filename or "unnamed.pdf",
            raw_text=raw_text,
        )
        document = await repository.add_document(session, document)
        await session.commit()
        await session.refresh(document, attribute_names=["chunks"])
        response = CVDocumentRead.model_validate(document)

    await arq_pool.enqueue_job("chunk_and_embed_cv", str(document.id))
    return response


@router.get("/documents", response_model=list[CVDocumentRead])
async def get_cv_documents(
    kind: CVDocumentKind | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CVDocumentRead]:
    async with SessionLocal() as session:
        documents = await repository.list_documents_with_chunks(
            session, kind=kind, limit=limit, offset=offset
        )
        return [CVDocumentRead.model_validate(d) for d in documents]


@router.get("/documents/{document_id}", response_model=CVDocumentRead)
async def get_cv_document(document_id: uuid.UUID) -> CVDocumentRead:
    async with SessionLocal() as session:
        document = await repository.get_document_with_chunks(session, document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="CV document not found")
        return CVDocumentRead.model_validate(document)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cv_document(document_id: uuid.UUID) -> None:
    async with SessionLocal() as session:
        deleted = await repository.delete_document(session, document_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="CV document not found")
        await session.commit()


@router.get("/events", include_in_schema=False)
async def cv_events(
    request: Request,
    redis: Annotated[Redis, Depends(get_redis)],
) -> StreamingResponse:
    """SSE stream of CvProcessingEvent JSON frames."""
    return sse_response(request, redis, EVENTS_CV)
