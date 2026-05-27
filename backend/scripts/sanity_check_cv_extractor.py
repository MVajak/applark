"""Sanity-check the CV chunker agent against the real Anthropic API.

Run from the backend/ directory:

    uv run python scripts/sanity_check_cv_extractor.py

Requires ANTHROPIC_API_KEY set in backend/.env.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings

SAMPLE_CV = """\
Jane Doe — Senior Frontend Engineer
jane@example.com

Summary
Frontend engineer with 8 years of experience in React and TypeScript,
specializing in design systems and large-scale applications.

Experience
Acme Corp — Senior Frontend Engineer (Jan 2022 — present)
- Led migration from Webpack to Vite, cutting build times by 60%
- Designed the company's first cross-product design system

Education
University of Helsinki (2014), BSc Computer Science

Tools — TypeScript, React, Vite, Tailwind, Playwright

Languages — English (native), Finnish (fluent)
"""


async def main() -> None:
    if not settings.ANTHROPIC_API_KEY:
        sys.exit(
            "ANTHROPIC_API_KEY is empty in backend/.env. "
            "Add a real key and rerun this script."
        )
    os.environ["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY

    # Import lazily — Pydantic AI validates the API key at Agent construction.
    from app.core.llm import LLM_MODEL_FAST
    from app.modules.cv.agent import cv_extractor

    user_message = (
        f"<cv>\n{SAMPLE_CV}\n</cv>\n\n"
        "Extract structured chunks per the rules above."
    )
    result = await cv_extractor.run(user_message)

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
