"""Re-baseline the prompts.baseline.toml file for one or more modules.

Run this AFTER intentionally editing a module's prompts.py AND AFTER
verifying the eval still passes. Both should be committed together so
the audit trail in git matches the prompt change.

Usage:
    uv run python scripts/snapshot_prompts.py matching
    uv run python scripts/snapshot_prompts.py matching cover_letters
    uv run python scripts/snapshot_prompts.py --all
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.prompts.registry import current_hash, prompts_path

ALL_MODULES = ["cv", "jobs", "matching", "cover_letters", "cv_tailor", "interview_prep"]


def write_baseline(module: str) -> Path:
    hash_value = current_hash(module)
    baseline = prompts_path(module).parent / "prompts.baseline.toml"
    today = dt.date.today().isoformat()
    baseline.write_text(
        f'[prompts]\nhash = "{hash_value}"\nbaselined_at = "{today}"\n'
    )
    return baseline


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modules", nargs="*", help="module names (e.g. matching cv jobs)")
    parser.add_argument("--all", action="store_true", help="snapshot every module")
    args = parser.parse_args()

    modules = ALL_MODULES if args.all else args.modules
    if not modules:
        parser.error("pass module names or --all")

    unknown = [m for m in modules if m not in ALL_MODULES]
    if unknown:
        parser.error(f"unknown modules: {unknown}. Valid: {ALL_MODULES}")

    for module in modules:
        path = write_baseline(module)
        print(f"baselined {module}: hash={current_hash(module)} → {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
