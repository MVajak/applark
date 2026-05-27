"""Sanity-check the deterministic match-context builder. No LLM calls.

Usage (from backend/):

    uv run python scripts/sanity_check_match_context.py <job_id>

Prints the MatchContext as JSON. Eyeball whether each requirement's top
chunks look intuitive (e.g. a "React" requirement should pick a React-
flavoured CV chunk first).

Requires:
  - One CV uploaded and chunked + embedded (POST /api/v1/cv/documents,
    worker run, status=ready in cv_chunks).
  - One job extracted (POST /api/v1/jobs/from-text or /from-url, worker
    run, status='ready', embeddings present on job + requirements).
"""

import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.modules.matching.service import (
    MissingEmbeddingsError,
    NoCVUploadedError,
    build_match_context,
)


async def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: sanity_check_match_context.py <job_id>")
    try:
        job_id = uuid.UUID(sys.argv[1])
    except ValueError:
        sys.exit(f"invalid UUID: {sys.argv[1]}")

    try:
        async with SessionLocal() as session:
            context = await build_match_context(session, job_id)
    except NoCVUploadedError as exc:
        sys.exit(f"no CV: {exc}")
    except MissingEmbeddingsError as exc:
        sys.exit(f"missing embeddings: {exc}")
    except RuntimeError as exc:
        sys.exit(f"error: {exc}")

    print(context.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
