from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModelSettings

from app.core.llm import LLM_MODEL_FAST
from app.modules.jobs.schemas import JobExtraction
from app.prompts import load_prompt

job_extractor: Agent[None, JobExtraction] = Agent(
    model=LLM_MODEL_FAST,
    output_type=JobExtraction,
    system_prompt=load_prompt("jobs").text,
    # Allow a couple of self-correction passes if the first output fails
    # Pydantic validation (e.g. transient missing-field hallucinations).
    retries=2,
    model_settings=AnthropicModelSettings(
        # Marks the system prompt as cacheable (PLAN.md §9.13).
        # NOTE: Anthropic's cache minimum is 4096 tokens for Haiku 4.5
        # (1024 for Sonnet/Opus). The job system prompt is ~2280 tokens,
        # so today this setting is a no-op — kept in place so it activates
        # automatically if examples grow or we move to Sonnet.
        anthropic_cache_instructions=True,
        # Dense postings (many requirements + responsibilities) can blow past
        # a 2000-token output. 8000 is a sane cap — worst-case Haiku ~$0.04.
        max_tokens=8000,
    ),
)
