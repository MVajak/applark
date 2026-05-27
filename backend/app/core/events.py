"""Redis pub/sub plumbing for push-based event streams.

Producers (ARQ worker tasks + service helpers) call ``publish`` after every
state transition that the UI cares about. Consumers (SSE routes) iterate
``subscribe`` and forward each JSON frame to the client. The pub/sub channel
is the single fan-out point so multiple FastAPI processes can each hold open
client connections without coordinating directly.
"""

import asyncio
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any, Final, cast

import structlog
from fastapi import Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from redis.asyncio import Redis
from redis.asyncio.client import PubSub

logger = structlog.get_logger(__name__)

EVENTS_JOBS: Final[str] = "events:jobs"
EVENTS_CV: Final[str] = "events:cv"

SSE_KEEPALIVE_SECONDS: Final[float] = 25.0


async def publish(redis: Redis, channel: str, event: BaseModel) -> None:
    """Serialize ``event`` to JSON and PUBLISH it on ``channel``.

    Best-effort: if Redis is down we log and swallow rather than failing the
    producing task. Status state is still persisted in Postgres, so the worst
    case is the UI falling back to its next manual refresh.
    """
    payload = event.model_dump_json()
    try:
        await cast("Any", redis).publish(channel, payload)
    except Exception:
        logger.exception("event_publish_failed", channel=channel)


async def subscribe(redis: Redis, channel: str) -> AsyncGenerator[str]:
    """Yield JSON payloads published on ``channel`` until the caller stops.

    The pubsub object is closed on generator teardown so client disconnects
    don't leak Redis connections.
    """
    # redis-py's pubsub returns a generic typed-as-Any object — narrow at this
    # boundary so the rest of the code stays strict.
    pubsub: PubSub = cast("Any", redis).pubsub()
    await cast("Any", pubsub).subscribe(channel)
    try:
        listener = cast("AsyncIterator[dict[str, Any]]", cast("Any", pubsub).listen())
        async for raw_message in listener:
            message: dict[str, Any] = raw_message
            if message.get("type") != "message":
                continue
            data = message.get("data")
            if isinstance(data, bytes):
                yield data.decode("utf-8")
            elif isinstance(data, str):
                yield data
    finally:
        await cast("Any", pubsub).unsubscribe(channel)
        await cast("Any", pubsub).aclose()


def sse_response(request: Request, redis: Redis, channel: str) -> StreamingResponse:
    """Wrap a Redis pub/sub subscription as a text/event-stream response.

    Emits ``data: <json>\\n\\n`` for each published event and ``: keepalive\\n\\n``
    every ``SSE_KEEPALIVE_SECONDS`` so idle connections don't get reaped by
    intermediaries. Detects client disconnect via ``request.is_disconnected``
    and cleans up the pub/sub on teardown.
    """

    async def gen() -> AsyncIterator[bytes]:
        events = subscribe(redis, channel)
        # Wrap anext() in a long-lived task so the keepalive timer can race it
        # without cancelling the underlying pubsub subscription on timeout —
        # asyncio.wait_for would tear down the subscribe() generator.

        async def _next() -> str:
            return await anext(events)

        next_task: asyncio.Task[str] = asyncio.create_task(_next())
        try:
            while True:
                if await request.is_disconnected():
                    return
                done, _ = await asyncio.wait(
                    {next_task}, timeout=SSE_KEEPALIVE_SECONDS
                )
                if not done:
                    yield b": keepalive\n\n"
                    continue
                try:
                    payload = next_task.result()
                except StopAsyncIteration:
                    return
                yield f"data: {payload}\n\n".encode()
                next_task = asyncio.create_task(_next())
        finally:
            next_task.cancel()
            await events.aclose()

    return StreamingResponse(gen(), media_type="text/event-stream")
