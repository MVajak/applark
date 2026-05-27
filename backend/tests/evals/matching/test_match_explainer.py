"""Eval suite for the match explainer — hits the real Anthropic API.

Skipped by default. Run with:

    uv run pytest tests/evals/matching/ --run-evals

Each case ships a hand-crafted context (job + candidate_chunks +
requirement_matches) and assertions over the agent's output (score
bounds, minimum strength/gap counts). Uses LLM_MODEL_SMART (Sonnet) —
~$0.04 per case.
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
async def test_match_explainer(case_file: Path) -> None:
    # Lazy import — Agent(...) eagerly validates the API key at construction.
    from app.modules.matching.agent import match_explainer

    case: dict[str, Any] = json.loads(case_file.read_text())
    ctx = case["context"]

    user_prompt = f"""<job>
{json.dumps(ctx["job"], indent=2)}
</job>

<candidate_chunks>
{json.dumps(ctx["candidate_chunks"], indent=2)}
</candidate_chunks>

<requirement_matches>
{json.dumps(ctx["requirement_matches"], indent=2)}
</requirement_matches>

Now produce a MatchExplanation per the rules in the system prompt."""

    result = await match_explainer.run(user_prompt)
    output = result.output
    expected: dict[str, Any] = case["expected"]

    if "min_score" in expected:
        assert output.overall_score >= expected["min_score"], (
            f"overall_score {output.overall_score} < min {expected['min_score']}"
        )

    if "max_score" in expected:
        assert output.overall_score <= expected["max_score"], (
            f"overall_score {output.overall_score} > max {expected['max_score']}"
        )

    if "min_strengths" in expected:
        assert len(output.strengths) >= expected["min_strengths"], (
            f"strengths count {len(output.strengths)} < min {expected['min_strengths']}"
        )

    if "min_gaps" in expected:
        assert len(output.gaps) >= expected["min_gaps"], (
            f"gaps count {len(output.gaps)} < min {expected['min_gaps']}"
        )
