from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModelSettings

from app.core.llm import LLM_MODEL_FAST
from app.modules.cv.schemas import CVExtraction
from app.prompts import load_prompt

cv_extractor: Agent[None, CVExtraction] = Agent(
    model=LLM_MODEL_FAST,
    output_type=CVExtraction,
    system_prompt=load_prompt("cv").text,
    # Allow a couple of self-correction passes if the first output fails
    # Pydantic validation (e.g. transient missing-field hallucinations).
    retries=2,
    model_settings=AnthropicModelSettings(
        # Marks the system prompt as cacheable (PLAN.md §9.13).
        # NOTE: Anthropic's cache minimum is 4096 tokens for Haiku 4.5
        # (1024 for Sonnet/Opus). The CV system prompt is ~1244 tokens,
        # so today this setting is a no-op — kept in place so it activates
        # automatically if the prompt grows or we move to Sonnet.
        anthropic_cache_instructions=True,
        # Real CVs (15+ chunks with metadata) easily blow past 2000 tokens.
        # 8000 is a sane cap — worst-case Haiku output cost ~$0.04.
        max_tokens=8000,
    ),
)
