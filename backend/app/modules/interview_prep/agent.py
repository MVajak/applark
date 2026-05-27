from pydantic_ai import Agent

from app.core.llm import LLM_MODEL_SMART, make_agent
from app.modules.interview_prep.schemas import InterviewPrepResult

# Reasoning model. ~10 questions (~120 tokens each) + role_overview + areas +
# the 4 questions_to_ask_them list; 4000 is a comfortable ceiling.
interview_prep_agent: Agent[None, InterviewPrepResult] = make_agent(
    "interview_prep", InterviewPrepResult, model=LLM_MODEL_SMART, max_tokens=4000
)
