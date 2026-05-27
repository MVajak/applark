from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModelSettings

from app.core.llm import LLM_MODEL_SMART
from app.modules.cover_letters.schemas import CoverLetterDraft
from app.prompts import load_prompt

cover_letter_drafter: Agent[None, CoverLetterDraft] = Agent(
    model=LLM_MODEL_SMART,
    output_type=CoverLetterDraft,
    system_prompt=load_prompt("cover_letters").text,
    # Allow one self-correction pass if the first output fails Pydantic
    # validation (e.g. missing required field).
    retries=2,
    model_settings=AnthropicModelSettings(
        # Marks the system prompt as cacheable (PLAN.md §9.13).
        # The prompt + 3 detailed examples easily clears Sonnet's 1024-token
        # minimum, so this saves ~90% of input tokens on repeat calls within
        # the 5-minute window.
        anthropic_cache_instructions=True,
        # 250-350-word letters are ~700 output tokens, but leave room for
        # the structured wrapper and the occasional longer body.
        max_tokens=3000,
    ),
)
