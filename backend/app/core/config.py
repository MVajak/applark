import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str

    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = True
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536

    LLM_MODEL_FAST: str = "anthropic:claude-haiku-4-5"
    LLM_MODEL_SMART: str = "anthropic:claude-sonnet-4-6"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()  # pyright: ignore[reportCallIssue]  # fields injected from .env

# Mirror provider keys into os.environ so SDKs that read them directly
# (Pydantic AI / Anthropic, OpenAI) pick them up without explicit api_key= args.
# Done here rather than in lifespan because Agent(...) eagerly validates the
# Anthropic key at module import.
for _var in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
    _value = getattr(settings, _var)
    if _value:
        os.environ.setdefault(_var, _value)
