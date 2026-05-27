from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModelSettings

from app.core.llm import LLM_MODEL_SMART
from app.modules.cv_tailor.schemas import CVTailorResult
from app.prompts import load_prompt

cv_tailor: Agent[None, CVTailorResult] = Agent(
    model=LLM_MODEL_SMART,
    output_type=CVTailorResult,
    system_prompt=load_prompt("cv_tailor").text,
    # One self-correction pass if the first output fails Pydantic validation
    # (e.g. an invalid UUID or missing required field).
    retries=2,
    model_settings=AnthropicModelSettings(
        # Marks the system prompt as cacheable (PLAN.md §9.13). The prompt
        # plus the 3 detailed examples is well above Sonnet's 1024-token
        # cache minimum so subsequent calls within 5 min get ~90% off the
        # input portion.
        anthropic_cache_instructions=True,
        # 3-7 suggestions, ~200 tokens each, + do_not_suggest list + summary
        # tops out well below this cap; keep headroom for the structured
        # wrapper.
        max_tokens=3000,
    ),
)
