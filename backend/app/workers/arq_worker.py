from typing import Any, ClassVar, cast

from arq.connections import RedisSettings
from redis.asyncio import Redis

from app.core.config import settings
from app.modules.cv.tasks import chunk_and_embed_cv
from app.modules.jobs.tasks import extract_job, scrape_and_extract_job


async def _on_startup(ctx: dict[str, Any]) -> None:
    """Attach a plain redis client to ARQ's ctx so tasks can PUBLISH events."""
    ctx["redis"] = cast("Redis", cast("Any", Redis).from_url(settings.REDIS_URL))


async def _on_shutdown(ctx: dict[str, Any]) -> None:
    client = ctx.get("redis")
    if isinstance(client, Redis):
        await client.aclose()


class WorkerSettings:
    functions: ClassVar = [chunk_and_embed_cv, extract_job, scrape_and_extract_job]
    redis_settings: ClassVar = RedisSettings.from_dsn(settings.REDIS_URL)
    max_tries: ClassVar[int] = 3
    job_timeout: ClassVar[int] = 120
    on_startup: ClassVar = _on_startup
    on_shutdown: ClassVar = _on_shutdown
