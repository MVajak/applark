from openai import AsyncOpenAI

from app.core.config import settings

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    """Lazily instantiate the OpenAI client.

    Lazy so module import doesn't require OPENAI_API_KEY — only the first
    call to get_embedding(s) does.
    """
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set in backend/.env")
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def get_embedding(text: str) -> list[float]:
    """Return a 1536-d embedding for ``text`` via OpenAI text-embedding-3-small."""
    [embedding] = await get_embeddings([text])
    return embedding


async def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Return 1536-d embeddings for all ``texts`` in a single API call.

    OpenAI's embeddings endpoint accepts a list of inputs and returns them
    in order — one round-trip instead of N when chunking a CV or processing
    a job's requirements.
    """
    if not texts:
        return []
    client = _get_client()
    response = await client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=texts,
    )
    # response.data is ordered to match the input list per OpenAI's contract.
    return [item.embedding for item in response.data]
