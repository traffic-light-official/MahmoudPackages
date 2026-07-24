"""Querying the status of an idempotency key.

Useful for a client that wants to poll "did my earlier request finish
yet?" without resending it, or for an internal admin/debugging endpoint.
"""

from __future__ import annotations

from drf_idempotency.core import get_backend


def get_idempotency_status(key: str) -> str | None:
    """Return the current status of an idempotency key.

    Args:
        key: The idempotency key to look up.

    Returns:
        ``"in_progress"``, ``"completed"``, or ``None`` if the key is
        unknown (never used, or its record has expired). Note that a
        request that failed (raised an exception, or produced an
        uncached error response) releases its key entirely — see
        ``docs/architecture.md`` — so a failed attempt is indistinguishable
        from "never attempted" via this function; that is by design, since
        it means the key remains free for a fresh, successful attempt.
    """
    record = get_backend().get(key)
    return record.status if record is not None else None
