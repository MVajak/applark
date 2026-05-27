from pydantic_ai import Agent

from app.core.llm import LLM_MODEL_FAST, make_agent
from app.modules.jobs.schemas import JobExtraction

# Fast extraction model. Dense postings (many requirements + responsibilities)
# can blow past a 2000-token output, so cap at 8000 (worst-case Haiku ~$0.04).
job_extractor: Agent[None, JobExtraction] = make_agent(
    "jobs", JobExtraction, model=LLM_MODEL_FAST, max_tokens=8000
)
