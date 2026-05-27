import pydantic_ai
import pytest

from app.prompts.registry import baseline_hash, current_hash

# Modules that have an evals/<module>/ tests folder. Add new ones here as
# coverage grows. Listed explicitly so prompt-divergence-gating only fires
# for modules that actually have an eval to re-run.
EVAL_MODULES = ("cv", "jobs", "matching")

# Default: forbid real LLM API requests in tests so accidental hits fail loudly.
# pytest_configure flips this to True if --run-evals is passed OR a prompt
# has drifted from its baseline (and thus its eval is being force-run).
pydantic_ai.models.ALLOW_MODEL_REQUESTS = False


def divergent_modules() -> set[str]:
    """Modules whose current prompts.py hash differs from the recorded baseline."""
    divergent: set[str] = set()
    for module in EVAL_MODULES:
        baseline = baseline_hash(module)
        if baseline is None:
            continue
        if current_hash(module) != baseline:
            divergent.add(module)
    return divergent


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-evals",
        action="store_true",
        default=False,
        help="Run @pytest.mark.evals tests that hit real LLM APIs (costs money).",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "evals: tests that hit real LLM APIs; opt in with --run-evals",
    )
    # Allow real LLM calls when the user opted in OR when a prompt drift will
    # force at least one eval to run anyway.
    if config.getoption("--run-evals") or divergent_modules():
        pydantic_ai.models.ALLOW_MODEL_REQUESTS = True


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--run-evals"):
        return  # User opted in — run everything as-is.

    forced = divergent_modules()
    skip_evals = pytest.mark.skip(reason="needs --run-evals option to run")
    for item in items:
        if "evals" not in item.keywords:
            continue
        # Skip evals UNLESS this test belongs to a module whose prompt drifted
        # from baseline — in which case force-run it so prompt changes can't
        # silently land without re-validating their agent.
        if forced and any(f"/evals/{module}/" in str(item.path) for module in forced):
            continue
        item.add_marker(skip_evals)
