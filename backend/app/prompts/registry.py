"""Versioned prompt registry.

Each feature module owns a `prompts.py` file with `SYSTEM_PROMPT` and
`EXAMPLES` string constants. This registry wraps that import with two
things every agent needs but nobody wants to write per-agent:

1. **Hash tracking.** `current_hash("matching")` returns a stable
   12-char sha256 of the entire `prompts.py` file. The hash is the
   identity of the prompt for purposes of "did this change?"

2. **Formatted text.** `load_prompt("matching").text` returns
   `SYSTEM_PROMPT.format(EXAMPLES=EXAMPLES)` — the system prompt every
   agent constructor takes — so agents never touch `.format` directly.

The baseline hash for each module lives at
`app/modules/<X>/prompts.baseline.toml`. Drift between baseline and
current hash is the signal that an eval needs to re-run; that gate
lives in `tests/test_prompts_baselined.py`.
"""

from __future__ import annotations

import hashlib
import importlib
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PromptHandle:
    """A loaded prompt + the hash of the prompts.py source file it came from."""

    module: str
    text: str
    hash: str


def prompts_path(module: str) -> Path:
    """Return the filesystem path to a module's prompts.py."""
    prompts_module = importlib.import_module(f"app.modules.{module}.prompts")
    if prompts_module.__file__ is None:
        raise RuntimeError(f"app.modules.{module}.prompts has no __file__")
    return Path(prompts_module.__file__)


def current_hash(module: str) -> str:
    """sha256 of the module's prompts.py, truncated to 12 hex chars."""
    return hashlib.sha256(prompts_path(module).read_bytes()).hexdigest()[:12]


def baseline_hash(module: str) -> str | None:
    """Read the recorded baseline hash from prompts.baseline.toml.

    Returns None if the baseline file doesn't exist yet (first-time
    setup for a module). Tests treat that as "no baseline recorded".
    """
    baseline = prompts_path(module).parent / "prompts.baseline.toml"
    if not baseline.exists():
        return None
    data = tomllib.loads(baseline.read_text())
    hash_value = data.get("prompts", {}).get("hash")
    return hash_value if isinstance(hash_value, str) else None


def load_prompt(module: str) -> PromptHandle:
    """Load the module's prompt and report its current hash.

    Convention: every module exports `SYSTEM_PROMPT` (a format string
    with a single `{EXAMPLES}` placeholder) and `EXAMPLES` (the
    in-context examples block). The returned `text` already has
    EXAMPLES interpolated, so agents pass it straight to
    `system_prompt=`.
    """
    prompts_module = importlib.import_module(f"app.modules.{module}.prompts")
    system_prompt = prompts_module.SYSTEM_PROMPT
    examples = prompts_module.EXAMPLES
    if not isinstance(system_prompt, str) or not isinstance(examples, str):
        raise TypeError(
            f"app.modules.{module}.prompts must define SYSTEM_PROMPT and EXAMPLES as strings"
        )
    text = system_prompt.format(EXAMPLES=examples)
    return PromptHandle(module=module, text=text, hash=current_hash(module))
