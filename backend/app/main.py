from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, cast

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from redis.asyncio import Redis

from app.api.v1.router import router as v1_router
from app.core import providers
from app.core.config import settings
from app.modules.cv import service as cv_service
from app.modules.cv.protocols import CVProvider
from app.modules.jobs import service as jobs_service
from app.modules.jobs.protocols import JobProvider
from app.modules.matching import service as matching_service
from app.modules.matching.protocols import MatchingProvider

# Bind each domain's service to its cross-module Protocol. Cross-module
# consumers resolve via `providers.get(SomeProvider)` instead of importing
# the service directly — and never reach another module's repository. Tests
# can re-register with fakes.
providers.register(CVProvider, cv_service)
providers.register(JobProvider, jobs_service)
providers.register(MatchingProvider, matching_service)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    app.state.arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    app.state.redis = cast("Redis", cast("Any", Redis).from_url(settings.REDIS_URL))
    try:
        yield
    finally:
        await app.state.redis.aclose()
        await app.state.arq_pool.aclose()


def _operation_id(route: APIRoute) -> str:
    """Use the route handler's function name as the OpenAPI operationId.

    Keeps orval-generated frontend hooks short and stable
    (``useGetJobs`` instead of ``useListJobsApiV1JobsGet``).
    """
    return route.name


app = FastAPI(
    title="Applark",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    lifespan=lifespan,
    generate_unique_id_function=_operation_id,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")
