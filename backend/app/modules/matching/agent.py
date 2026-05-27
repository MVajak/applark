from pydantic_ai import Agent

from app.core.llm import LLM_MODEL_SMART, make_agent
from app.modules.matching.schemas import MatchExplanation

# Reasoning model; output is larger than extraction (strengths + gaps +
# emphasis), so allow 3000 tokens. Keeps Pydantic AI's default single attempt
# (retries=1) rather than the self-correction retry the other agents use.
match_explainer: Agent[None, MatchExplanation] = make_agent(
    "matching", MatchExplanation, model=LLM_MODEL_SMART, max_tokens=3000, retries=1
)
