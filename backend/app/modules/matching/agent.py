from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModelSettings

from app.core.llm import LLM_MODEL_SMART
from app.modules.matching.schemas import MatchExplanation
from app.prompts import load_prompt

match_explainer: Agent[None, MatchExplanation] = Agent(
    model=LLM_MODEL_SMART,
    output_type=MatchExplanation,
    system_prompt=load_prompt("matching").text,
    model_settings=AnthropicModelSettings(
        # Sonnet's cache minimum is 1024 tokens (vs Haiku's 4096), and this
        # prompt + 3 detailed examples is well above that — caching will
        # actually fire here for the first time in the project.
        anthropic_cache_instructions=True,
        # Matching output is structurally larger than extraction (multiple
        # strengths + gaps + emphasis list) — give it more room than the
        # 2000-token cap on the extractors.
        max_tokens=3000,
    ),
)
