from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModelSettings

from app.core.llm import LLM_MODEL_SMART
from app.modules.interview_prep.schemas import InterviewPrepResult
from app.prompts import load_prompt

interview_prep_agent: Agent[None, InterviewPrepResult] = Agent(
    model=LLM_MODEL_SMART,
    output_type=InterviewPrepResult,
    system_prompt=load_prompt("interview_prep").text,
    # One self-correction pass if the first output fails Pydantic validation.
    retries=2,
    model_settings=AnthropicModelSettings(
        # Marks the system prompt as cacheable (PLAN.md §9.13). The prompt
        # plus three worked examples is well above Sonnet's 1024-token cache
        # minimum, so repeat calls within 5 min get ~90% off the input side.
        anthropic_cache_instructions=True,
        # 10 questions, each ~120 tokens, plus role_overview + areas + the
        # 4 questions_to_ask_them list. 4000 is a comfortable ceiling.
        max_tokens=4000,
    ),
)
