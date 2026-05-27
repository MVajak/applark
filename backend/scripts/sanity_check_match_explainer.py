"""Sanity-check the match explainer agent with a hand-built input.

Run from backend/:

    uv run python scripts/sanity_check_match_explainer.py

Uses LLM_MODEL_SMART (Sonnet 4.6). One call is ~$0.02-0.05.
Requires ANTHROPIC_API_KEY in backend/.env.

The constructed scenario is a medium/partial fit so the agent has to
make real judgement calls (some required overlap, one clear gap).
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings

JOB: dict[str, Any] = {
    "title": "Senior Frontend Engineer",
    "company": "Bubblydoo",
    "location": "Antwerp, Belgium",
    "remote_policy": "hybrid",
    "seniority": "senior",
    "tech_stack": ["typescript", "next.js", "tailwind", "trpc"],
    "summary": (
        "Senior frontend role at a small Antwerp-based product team building "
        "creative tools for designers. Ship features end-to-end, collaborate "
        "closely with designers, contribute to the design system."
    ),
}

CANDIDATE_CHUNKS: list[dict[str, Any]] = [
    {
        "cv_chunk_id": "11111111-1111-1111-1111-111111111111",
        "chunk_type": "summary",
        "content": "8 years building React applications, including a year as feature lead at Katana MRP",
        "metadata": {},
        "similarity": 0.79,
    },
    {
        "cv_chunk_id": "22222222-2222-2222-2222-222222222222",
        "chunk_type": "experience",
        "content": "Senior Frontend Engineer at Katana MRP — Led migration from Webpack to Vite, cutting build times 60% and CI minutes 40%",
        "metadata": {"company": "Katana MRP", "role": "Senior Frontend Engineer"},
        "similarity": 0.74,
    },
    {
        "cv_chunk_id": "33333333-3333-3333-3333-333333333333",
        "chunk_type": "experience",
        "content": "Planned and shipped a 170-ticket ingredient booking feature as feature lead at Katana, including Miro architecture diagrams and weekly cross-team syncs",
        "metadata": {"company": "Katana MRP"},
        "similarity": 0.66,
    },
    {
        "cv_chunk_id": "44444444-4444-4444-4444-444444444444",
        "chunk_type": "skill",
        "content": "TypeScript, React, Vite, TanStack Query, Tailwind, Playwright",
        "metadata": {},
        "similarity": 0.72,
    },
    {
        "cv_chunk_id": "55555555-5555-5555-5555-555555555555",
        "chunk_type": "experience",
        "content": "Built a JWT/OTP auth flow from scratch at ObsidianOS, covering token rotation and rate-limited OTP delivery",
        "metadata": {"company": "ObsidianOS"},
        "similarity": 0.41,
    },
]

REQUIREMENT_MATCHES: list[dict[str, Any]] = [
    {
        "requirement_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "requirement_text": "5+ years of frontend experience",
        "category": "required",
        "top_chunks": [
            {
                "cv_chunk_id": "11111111-1111-1111-1111-111111111111",
                "content": "8 years building React applications, including a year as feature lead at Katana MRP",
                "similarity": 0.81,
            }
        ],
    },
    {
        "requirement_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "requirement_text": "Strong TypeScript fundamentals",
        "category": "required",
        "top_chunks": [
            {
                "cv_chunk_id": "44444444-4444-4444-4444-444444444444",
                "content": "TypeScript, React, Vite, TanStack Query, Tailwind, Playwright",
                "similarity": 0.84,
            }
        ],
    },
    {
        "requirement_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
        "requirement_text": "Experience with Next.js App Router",
        "category": "nice_to_have",
        "top_chunks": [
            {
                "cv_chunk_id": "44444444-4444-4444-4444-444444444444",
                "content": "TypeScript, React, Vite, TanStack Query, Tailwind, Playwright",
                "similarity": 0.46,
            }
        ],
    },
    {
        "requirement_id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
        "requirement_text": "Ship features end-to-end across product and design system",
        "category": "responsibility",
        "top_chunks": [
            {
                "cv_chunk_id": "33333333-3333-3333-3333-333333333333",
                "content": "Planned and shipped a 170-ticket ingredient booking feature as feature lead at Katana, including Miro architecture diagrams and weekly cross-team syncs",
                "similarity": 0.78,
            }
        ],
    },
]


async def main() -> None:
    if not settings.ANTHROPIC_API_KEY:
        sys.exit("ANTHROPIC_API_KEY is empty in backend/.env.")
    os.environ["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY

    # Lazy import — Agent(...) eagerly validates the API key at construction.
    from app.core.llm import LLM_MODEL_SMART
    from app.modules.matching.agent import match_explainer

    user_message = (
        f"<job>\n{json.dumps(JOB, indent=2)}\n</job>\n\n"
        f"<candidate_chunks>\n{json.dumps(CANDIDATE_CHUNKS, indent=2)}\n</candidate_chunks>\n\n"
        f"<requirement_matches>\n{json.dumps(REQUIREMENT_MATCHES, indent=2)}\n</requirement_matches>\n\n"
        "Now produce a MatchExplanation per the rules above."
    )
    result = await match_explainer.run(user_message)

    print("=" * 70)
    print("Structured output:")
    print("=" * 70)
    print(result.output.model_dump_json(indent=2))

    usage = result.usage()
    details = getattr(usage, "details", {}) or {}
    print("=" * 70)
    print(f"Model: {LLM_MODEL_SMART}")
    print(f"Tokens — input: {usage.input_tokens}  output: {usage.output_tokens}")
    print(
        f"  cache_creation_input_tokens: {details.get('cache_creation_input_tokens', 0)}"
    )
    print(
        f"  cache_read_input_tokens: {details.get('cache_read_input_tokens', 0)}"
    )


if __name__ == "__main__":
    asyncio.run(main())
