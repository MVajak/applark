"""Tests for the Redis pub/sub plumbing and the SSE response wrapper.

These hit a real Redis (per ``settings.REDIS_URL``). If Redis isn't reachable
the whole module is skipped — keeps the suite usable on machines without
``docker compose up``, while still catching regressions in the dev/CI flow
where Redis is always available.
"""

import asyncio
import json
import uuid
from typing import Any, cast
from unittest.mock import AsyncMock

import pytest
from fastapi import Request
from redis.asyncio import Redis

from app.core.config import settings
from app.core.events import (
    EVENTS_JOBS,
    SSE_KEEPALIVE_SECONDS,
    publish,
    sse_response,
    subscribe,
)
from app.modules.jobs.events import JobStatusEvent
from app.modules.jobs.schemas import JobStatus


async def _redis_or_skip() -> Redis:
    client: Redis = cast("Redis", cast("Any", Redis).from_url(settings.REDIS_URL))
    try:
        await cast("Any", client).ping()
    except Exception as exc:
        await client.aclose()
        pytest.skip(f"Redis unreachable at {settings.REDIS_URL}: {exc}")
    return client


async def test_publish_subscribe_roundtrip() -> None:
    redis = await _redis_or_skip()
    try:
        events = subscribe(redis, EVENTS_JOBS)

        async def _next() -> str:
            return await anext(events)

        # Drive the subscriber once so it actually registers with Redis before
        # we publish — otherwise the message is dropped.
        sub_task: asyncio.Task[str] = asyncio.create_task(_next())
        await asyncio.sleep(0.05)

        event = JobStatusEvent(job_id=uuid.uuid4(), status=JobStatus.ready)
        await publish(redis, EVENTS_JOBS, event)

        payload = await asyncio.wait_for(sub_task, timeout=2.0)
        assert json.loads(payload) == json.loads(event.model_dump_json())

        await events.aclose()
    finally:
        await redis.aclose()


async def test_sse_response_emits_data_frame() -> None:
    """The SSE response's body iterator should yield a ``data: <json>\\n\\n``
    frame for each event published on the channel.

    Drives ``sse_response`` directly rather than over ASGITransport — the
    in-process HTTP layer has quirks around ``is_disconnected`` that make the
    full-stack test flaky without adding any signal about the frame format.
    """
    redis = await _redis_or_skip()
    try:
        fake_request = AsyncMock(spec=Request)
        fake_request.is_disconnected = AsyncMock(return_value=False)
        request = cast("Request", fake_request)
        response = sse_response(request, redis, EVENTS_JOBS)
        body_iter = cast("Any", response).body_iterator

        async def _next_chunk() -> bytes:
            chunk = await anext(body_iter)
            if isinstance(chunk, str):
                return chunk.encode()
            assert isinstance(chunk, bytes)
            return chunk

        # Give the route's pubsub a beat to subscribe, then publish.
        next_task: asyncio.Task[bytes] = asyncio.create_task(_next_chunk())
        await asyncio.sleep(0.1)
        event = JobStatusEvent(job_id=uuid.uuid4(), status=JobStatus.extracting)
        await publish(redis, EVENTS_JOBS, event)

        chunk = await asyncio.wait_for(next_task, timeout=2.0)
        text = chunk.decode()
        assert text.startswith("data: ")
        assert text.endswith("\n\n")
        payload = text.removeprefix("data: ").rstrip("\n")
        assert json.loads(payload) == json.loads(event.model_dump_json())

        await body_iter.aclose()
    finally:
        await redis.aclose()


def test_sse_keepalive_constant_is_under_proxy_idle_window() -> None:
    # Most defaults (nginx 60s, ALB 60s, Cloudflare 100s) — 25s is a safe
    # margin. Locking the value down so a future tweak can't silently push
    # past the threshold.
    assert SSE_KEEPALIVE_SECONDS <= 30
