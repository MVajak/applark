"""Eval suite for the CV chunker agent — hits the real Anthropic API.

Skipped by default. Run with:

    uv run pytest tests/evals/cv/ --run-evals

Requires ANTHROPIC_API_KEY in backend/.env.
"""

import json
from pathlib import Path
from typing import Any

import pytest

EVAL_DIR = Path(__file__).parent
EVAL_FILES = sorted(EVAL_DIR.glob("*.json"))


@pytest.mark.evals
@pytest.mark.parametrize(
    "case_file",
    EVAL_FILES,
    ids=[f.stem for f in EVAL_FILES],
)
async def test_cv_extractor(case_file: Path) -> None:
    # Lazy import — Agent(...) eagerly validates the API key at construction.
    from app.modules.cv.agent import cv_extractor

    case: dict[str, Any] = json.loads(case_file.read_text())
    user_message = f"<cv>\n{case['input']}\n</cv>\n\nExtract structured chunks per the rules above."
    result = await cv_extractor.run(user_message)
    output = result.output
    expected: dict[str, Any] = case["expected"]

    if "candidate_name" in expected:
        assert output.candidate_name == expected["candidate_name"], (
            f"candidate_name: got {output.candidate_name!r}, "
            f"expected {expected['candidate_name']!r}"
        )

    if "languages_spoken" in expected:
        assert set(output.languages_spoken) == set(expected["languages_spoken"]), (
            f"languages_spoken: got {output.languages_spoken}, "
            f"expected {expected['languages_spoken']}"
        )

    if "chunk_types_present" in expected:
        actual = {chunk.chunk_type.value for chunk in output.chunks}
        missing = set(expected["chunk_types_present"]) - actual
        assert not missing, f"Missing chunk types: {missing}. Got: {actual}"
