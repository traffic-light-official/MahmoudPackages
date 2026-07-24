"""The storage backend interface every backend implements.

A backend is responsible for exactly one thing: atomically deciding, for
a given idempotency key, whether the *current* request is the first to
use that key (in which case it should proceed and eventually call
:meth:`BaseBackend.complete`), or whether a prior request already claimed
it (in which case its stored result — or in-progress status — should be
returned instead).

That single atomic decision is what :meth:`BaseBackend.acquire_or_get`
returns. Every other method is a straightforward read or write keyed by
the idempotency key.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass(frozen=True, slots=True)
class StoredRecord:
    """The stored state of one idempotency key.

    Attributes:
        key: The idempotency key this record belongs to.
        fingerprint: The fingerprint of the request that first used this
            key (see :func:`drf_idempotency.fingerprint.compute_fingerprint`).
        status: One of ``"in_progress"``, ``"completed"``, or ``"failed"``.
        response_status_code: The stored response's HTTP status code, or
            ``None`` if ``status`` is ``"in_progress"``.
        response_headers: The stored response's headers, or ``None`` if
            ``status`` is ``"in_progress"``.
        response_body: The stored response's raw body bytes, or ``None``
            if ``status`` is ``"in_progress"``.
        created_at: When the key was first claimed.
    """

    key: str
    fingerprint: str
    status: str
    response_status_code: int | None
    response_headers: Mapping[str, str] | None
    response_body: bytes | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AcquireResult:
    """The outcome of calling :meth:`BaseBackend.acquire_or_get`.

    Attributes:
        acquired: ``True`` if this call claimed the key and the caller
            should proceed to execute the request (and later call
            :meth:`BaseBackend.complete` or :meth:`BaseBackend.fail`).
            ``False`` if another request already holds or has completed
            this key.
        existing: The current stored record, populated whenever
            ``acquired`` is ``False``. ``None`` when ``acquired`` is
            ``True``.
    """

    acquired: bool
    existing: StoredRecord | None


class BaseBackend(ABC):
    """Abstract base class for idempotency storage backends.

    Subclass this and implement every abstract method to add a new
    storage backend. See :class:`drf_idempotency.backends.redis.RedisBackend`
    and :class:`drf_idempotency.backends.database.DatabaseBackend` for
    reference implementations.

    Args:
        **options: Backend-specific keyword arguments, passed through from
            the ``BACKEND_OPTIONS`` setting.
    """

    def __init__(self, **options: Any) -> None:
        self.options = options

    @abstractmethod
    def acquire_or_get(self, key: str, fingerprint: str, *, lock_ttl: timedelta) -> AcquireResult:
        """Atomically claim ``key``, or return its current state.

        This is the operation race-safety depends on: if two requests
        call this concurrently with the same ``key``, exactly one must
        receive ``AcquireResult(acquired=True, existing=None)`` and the
        other(s) must receive ``AcquireResult(acquired=False, existing=...)``.

        Args:
            key: The idempotency key to claim.
            fingerprint: The requesting request's fingerprint, stored
                alongside the key if this call acquires it.
            lock_ttl: How long the claim is held before it's considered
                abandoned and eligible to be reclaimed by a later call.

        Returns:
            An :class:`AcquireResult` describing whether this call
            claimed the key.
        """

    @abstractmethod
    def complete(
        self,
        key: str,
        *,
        status_code: int,
        headers: Mapping[str, str],
        body: bytes,
        ttl: timedelta,
    ) -> None:
        """Store the final response for a successfully-processed request.

        Args:
            key: The idempotency key (must currently be held by the
                caller, i.e. previously returned ``acquired=True``).
            status_code: The HTTP status code to replay on future lookups.
            headers: The HTTP headers to replay.
            body: The raw response body bytes to replay.
            ttl: How long the completed record remains eligible for
                replay before it expires.
        """

    @abstractmethod
    def fail(self, key: str) -> None:
        """Release a claimed key without storing a response.

        Called when request processing raised an unhandled exception or
        produced a server error (5xx) that should not be cached — the key
        becomes available for a fresh attempt.

        Args:
            key: The idempotency key to release.
        """

    @abstractmethod
    def get(self, key: str) -> StoredRecord | None:
        """Look up a key's current record without claiming it.

        Args:
            key: The idempotency key to look up.

        Returns:
            The current :class:`StoredRecord`, or ``None`` if the key is
            unknown (or has expired).
        """

    @abstractmethod
    def cleanup_expired(self) -> int:
        """Remove expired records.

        For backends with native TTL support (e.g. Redis), this is
        typically a no-op returning ``0``, since expiry is handled by the
        store itself. For backends without native expiry (e.g. the
        database backend), this performs the actual deletion and should
        be called periodically — see the ``cleanup_expired_idempotency_keys``
        management command.

        Returns:
            The number of records removed.
        """
