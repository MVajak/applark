"""Tiny dict-based registry for cross-module providers.

Each domain defines a `Protocol` in `app/modules/<X>/protocols.py`
describing the surface it exposes to other domains. At startup
(`app/main.py`) the concrete implementation — the module's `service` —
is registered against the protocol. Consumer services pull via
`providers.get(SomeProvider)` instead of importing the implementation
directly, so a module's `repository` is never reached from outside its
own service.

The point isn't dependency injection ceremony; it's that
`grep "from app.modules.cv"` in another module returns only the
Protocol import, not the implementation. That makes cross-module
seams explicit and makes mocking in tests trivial
(`providers.register(CVProvider, fake)`).

Implementations of these protocols are a `service` module (a
module-level set of `async def` functions). Protocols are structural
in Python, so the module just needs to define the same functions — no
explicit `implements`.
"""

from __future__ import annotations

_registry: dict[type, object] = {}


def register[T](protocol: type[T], impl: T) -> None:
    """Bind an implementation to a protocol. Overwrites if already present."""
    _registry[protocol] = impl


def get[T](protocol: type[T]) -> T:
    """Look up an implementation. Raises KeyError if nothing is registered."""
    if protocol not in _registry:
        raise KeyError(
            f"No implementation registered for {protocol.__name__}. "
            "Did app.main register it at startup?"
        )
    # The Protocol is structural; the cast is safe by construction.
    return _registry[protocol]  # type: ignore[return-value]


def reset() -> None:
    """Clear the registry. Test-only — production never calls this."""
    _registry.clear()
