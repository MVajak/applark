from pydantic_ai import Agent

from app.core.llm import LLM_MODEL_FAST, make_agent
from app.modules.cv.schemas import CVExtraction

# Fast extraction model. Real CVs (15+ chunks with metadata) easily exceed a
# 2000-token output, so cap at 8000 (worst-case Haiku output ~$0.04).
cv_extractor: Agent[None, CVExtraction] = make_agent(
    "cv", CVExtraction, model=LLM_MODEL_FAST, max_tokens=8000
)
