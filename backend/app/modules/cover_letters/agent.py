from pydantic_ai import Agent

from app.core.llm import LLM_MODEL_SMART, make_agent
from app.modules.cover_letters.schemas import CoverLetterDraft

# Reasoning model. 250-350-word letters are ~700 output tokens; 3000 leaves
# room for the structured wrapper and the occasional longer body.
cover_letter_drafter: Agent[None, CoverLetterDraft] = make_agent(
    "cover_letters", CoverLetterDraft, model=LLM_MODEL_SMART, max_tokens=3000
)
