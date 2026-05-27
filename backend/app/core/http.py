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
