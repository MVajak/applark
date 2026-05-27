"""LLM model strings + the shared Pydantic AI agent factory.

Model strings resolve from settings so they can be swapped via env vars
without touching agent code (PLAN.md §9.8 — fast model for pure extraction,
smart model for reasoning-heavy agents). ``make_agent`` builds the uniform
agent shape every module needs, and ``extract_token_usage`` normalises the
token counts off a run result. ``agent.run()`` is still only called from
service.py.
"""

from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModelSettings
from pydantic_ai.usage import RunUsage

from app.core.config import settings
from app.prompts import load_prompt

LLM_MODEL_FAST: str = settings.LLM_MODEL_FAST
LLM_MODEL_SMART: str = settings.LLM_MODEL_SMART


def make_agent[T](
    module: str,
    output_type: type[T],
    *,
    model: str,
    max_tokens: int,
    retries: int = 2,
) -> Agent[None, T]:
    """Build a module's agent from its registered prompt.

    Every agent shares the same shape: no deps, an Anthropic model with
    cacheable system instructions, and a structured ``output_type``. Only the
    prompt ``module``, ``output_type``, ``model`` tier, ``max_tokens`` cap and
    ``retries`` count vary — pass those in.

    ``anthropic_cache_instructions`` is always set: it's a no-op below
    Anthropic's cache floor (4096 tokens for Haiku, 1024 for Sonnet) but
    activates for free once a prompt clears it.
    """
    return Agent(
        model=model,
        output_type=output_type,
        system_prompt=load_prompt(module).text,
        retries=retries,
        model_settings=AnthropicModelSettings(
            anthropic_cache_instructions=True,
            max_tokens=max_tokens,
        ),
    )


def extract_token_usage(usage: RunUsage) -> tuple[int | None, int | None]:
    """Return ``(input_tokens, output_tokens)`` from a Pydantic AI usage object.

    The field spellings have moved across pydantic-ai versions; read the
    current names with a fallback to the older ``request``/``response`` ones
    so every caller stays correct in one place if the pin ever moves.
    """
    input_tokens: int | None = getattr(usage, "input_tokens", None) or getattr(
        usage, "request_tokens", None
    )
    output_tokens: int | None = getattr(usage, "output_tokens", None) or getattr(
        usage, "response_tokens", None
    )
    return input_tokens, output_tokens
