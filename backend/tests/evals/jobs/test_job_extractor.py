"""Eval suite for the job extractor agent — hits the real Anthropic API.

Skipped by default. Run with:

    uv run pytest tests/evals/jobs/ --run-evals

Requires ANTHROPIC_API_KEY in backend/.env.
"""

import json
from pathlib import Path
from typing import Any

import pytest

EVAL_DIR = Path(__file__).parent
EVAL_FILES = sorted(EVAL_DIR.glob("*.json"))


def _normalize_tech(tech: str) -> str:
    """Lowercase + collapse spaces/underscores to hyphens for comparison."""
    return tech.lower().strip().replace(" ", "-").replace("_", "-")


@pytest.mark.evals
@pytest.mark.parametrize(
    "case_file",
    EVAL_FILES,
    ids=[f.stem for f in EVAL_FILES],
)
async def test_job_extractor(case_file: Path) -> None:
    # Lazy import — Agent(...) eagerly validates the API key at construction.
    from app.modules.jobs.agent import job_extractor

    case: dict[str, Any] = json.loads(case_file.read_text())
    user_message = (
        f"<job_posting>\n{case['input']}\n</job_posting>\n\n"
        "Extract the structured fields per the rules above."
    )
    result = await job_extractor.run(user_message)
    output = result.output
    expected: dict[str, Any] = case["expected"]

    if "title" in expected:
        assert output.title == expected["title"], (
            f"title: got {output.title!r}, expected {expected['title']!r}"
        )

    if "company" in expected:
        assert output.company == expected["company"], (
            f"company: got {output.company!r}, expected {expected['company']!r}"
        )

    if "remote_policy" in expected:
        assert output.remote_policy.value == expected["remote_policy"], (
            f"remote_policy: got {output.remote_policy.value}, expected {expected['remote_policy']}"
        )

    if "seniority" in expected:
        assert output.seniority.value == expected["seniority"], (
            f"seniority: got {output.seniority.value}, expected {expected['seniority']}"
        )

    if "tech_stack_includes" in expected:
        actual = {_normalize_tech(t) for t in output.tech_stack}
        needed = {_normalize_tech(t) for t in expected["tech_stack_includes"]}
        missing = needed - actual
        assert not missing, f"Missing tech: {missing}. Got: {actual}"

    if "salary_range" in expected:
        assert output.salary_range == expected["salary_range"], (
            f"salary_range: got {output.salary_range!r}, expected {expected['salary_range']!r}"
        )

    if "min_requirements" in expected:
        actual_count = len(output.requirements)
        min_count = expected["min_requirements"]
        assert actual_count >= min_count, f"requirements count {actual_count} < min {min_count}"
