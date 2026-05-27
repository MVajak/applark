from arq import ArqRedis
from fastapi import Request
from redis.asyncio import Redis


def get_arq_pool(request: Request) -> ArqRedis:
    """FastAPI dependency: return the ARQ Redis pool from app.state.

    The pool is created in main.py's lifespan handler. Raises if missing
    so misconfiguration fails loud.
    """
    pool = getattr(request.app.state, "arq_pool", None)
    if not isinstance(pool, ArqRedis):
        raise RuntimeError("ARQ pool not initialised — lifespan did not run")
    return pool


def get_redis(request: Request) -> Redis:
    """FastAPI dependency: plain redis.asyncio client for pub/sub.

    Separate from the ARQ pool because ArqRedis is a typed wrapper that
    doesn't expose the generic pub/sub commands the SSE routes need.
    """
    client = getattr(request.app.state, "redis", None)
    if not isinstance(client, Redis):
        raise RuntimeError("Redis client not initialised — lifespan did not run")
    return client
