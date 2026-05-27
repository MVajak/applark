"""Guard: every module's prompts.py must match the recorded baseline.

When a developer edits a prompts file, this test fails with the exact
re-baseline command. The eval for the affected module is also
force-enrolled in this pytest run (see conftest.py → divergent_modules)
so prompt changes can't slip through without re-validating the agent.
"""

from __future__ import annotations

import pytest

from app.prompts.registry import baseline_hash, current_hash

MODULES = ["cv", "jobs", "matching", "cover_letters", "cv_tailor", "interview_prep"]


@pytest.mark.parametrize("module", MODULES)
def test_prompts_match_baseline(module: str) -> None:
    baseline = baseline_hash(module)
    current = current_hash(module)
    if baseline is None:
        pytest.fail(
            f"No prompts.baseline.toml recorded for {module!r}. "
            f"Run: uv run python scripts/snapshot_prompts.py {module}"
        )
    assert current == baseline, (
        f"{module}/prompts.py changed since last baseline "
        f"(current={current}, baseline={baseline}).\n"
        f"After confirming the change is intentional:\n"
        f"  1. uv run python scripts/snapshot_prompts.py {module}\n"
        f"  2. uv run pytest --run-evals -k {module}  (or rely on the\n"
        f"     auto-forced eval in this run via conftest)\n"
        f"  3. Commit both the prompts.py edit and the new baseline together."
    )
