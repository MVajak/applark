"""LLM model strings used by Pydantic AI agents.

Resolves from settings so the model can be swapped via env vars without
touching agent code. See PLAN.md §9.8 — fast model for pure extraction,
smart model for reasoning-heavy agents.
"""

from app.core.config import settings

LLM_MODEL_FAST: str = settings.LLM_MODEL_FAST
LLM_MODEL_SMART: str = settings.LLM_MODEL_SMART
