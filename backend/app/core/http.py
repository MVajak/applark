"""Small HTTP helpers shared across routers."""

from collections.abc import Generator
from contextlib import contextmanager

from fastapi import HTTPException, status


@contextmanager
def conflict_on(*exc_types: type[Exception]) -> Generator[None]:
    """Map the given service exceptions to ``409 Conflict``.

    Routers wrap a service call so a domain precondition failure (e.g. "job
    not ready", "no match run yet") surfaces as a 409 with the exception's
    message as the detail::

        with conflict_on(NoMatchRunError, FeaturePrerequisitesError):
            draft = await service.generate_cover_letter(session, job_id)
    """
    try:
        yield
    except exc_types as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@contextmanager
def not_found_on(*exc_types: type[Exception]) -> Generator[None]:
    """Map the given service exceptions to ``404 Not Found``.

    The companion to :func:`conflict_on`: a router wraps a service call so a
    "no such row" domain error surfaces as a 404 with the exception's message
    as the detail::

        with not_found_on(JobNotFoundError):
            run = await run_match(session, job_id)
    """
    try:
        yield
    except exc_types as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
