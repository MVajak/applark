"""Sanity-check the job extractor agent against the real Anthropic API.

Run from the backend/ directory:

    uv run python scripts/sanity_check_job_extractor.py

Requires ANTHROPIC_API_KEY set in backend/.env. Replace SAMPLE_POSTING below
with a real posting you've copied recently if you want a realistic check.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings

SAMPLE_POSTING = """\
Senior Full-Stack Engineer at Finary (Paris, hybrid)

About Finary
Finary helps individuals track and grow their personal finances across
banks, brokers, and crypto accounts.

Stack: TypeScript, Next.js, Node.js, PostgreSQL, Redis, AWS.

What you'll work on:
- Ship features end-to-end across web and API
- Pair with designers, PMs, and other engineers
- Improve the performance of our financial data pipelines

Must have:
- 5+ years shipping production web applications
- Strong TypeScript and modern React
- Experience designing relational data models

Nice to have:
- Personal finance / fintech domain experience
- Familiarity with WebSockets for real-time updates

Compensation: €70-90k plus equity.
"""


async def main() -> None:
    if not settings.ANTHROPIC_API_KEY:
        sys.exit(
            "ANTHROPIC_API_KEY is empty in backend/.env. Add a real key and rerun this script."
        )
    os.environ["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY

    # Lazy import — Pydantic AI validates the API key at Agent construction.
    from app.core.llm import LLM_MODEL_FAST
    from app.modules.jobs.agent import job_extractor

    user_message = (
        f"<job_posting>\n{SAMPLE_POSTING}\n</job_posting>\n\n"
        "Extract the structured fields per the rules above."
    )
    result = await job_extractor.run(user_message)

    print("=" * 70)
    print("Structured output:")
    print("=" * 70)
    print(result.output.model_dump_json(indent=2))

    usage = result.usage()
    input_tokens = getattr(usage, "input_tokens", None) or getattr(usage, "request_tokens", None)
    output_tokens = getattr(usage, "output_tokens", None) or getattr(usage, "response_tokens", None)
    print("=" * 70)
    print(f"Tokens — input: {input_tokens} output: {output_tokens}")
    print(f"Model: {LLM_MODEL_FAST}")


if __name__ == "__main__":
    asyncio.run(main())
