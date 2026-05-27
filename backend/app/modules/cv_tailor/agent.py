from pydantic_ai import Agent

from app.core.llm import LLM_MODEL_SMART, make_agent
from app.modules.cv_tailor.schemas import CVTailorResult

# Reasoning model. 3-7 suggestions (~200 tokens each) + do_not_suggest +
# summary tops out well below 3000; the cap just keeps headroom.
cv_tailor: Agent[None, CVTailorResult] = make_agent(
    "cv_tailor", CVTailorResult, model=LLM_MODEL_SMART, max_tokens=3000
)
