"""Redis-backed idempotency storage.

Uses a single ``SET key value NX EX ttl`` command for atomic lock
acquisition — the same primitive Redis's own documentation recommends for
distributed locking — so no separate locking library is required.

Requires the ``redis`` extra: ``pip install drf-idempotency[redis]``.
"""

from __future__ import annotations

import base64
import json
from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Any

from django.utils import timezone

from drf_idempotency.backends.base import AcquireResult, BaseBackend, StoredRecord

try:
    import redis as redis_lib
except ImportError as exc:  # pragma: no cover - exercised via skip when redis is absent
    raise ImportError(
        "drf_idempotency.backends.redis requires the 'redis' package. "
        "Install it with: pip install drf-idempotency[redis]"
    ) from exc

_DEFAULT_KEY_PREFIX = "idempotency:"


class RedisBackend(BaseBackend):
    """Stores idempotency records in Redis.

    Args:
        url: A ``redis://`` connection URL. Ignored if ``client`` is
            given. Defaults to ``"redis://localhost:6379/0"``.
        client: An existing ``redis.Redis`` client instance to reuse
            (e.g. one already configured elsewhere in your project).
        key_prefix: Prefix applied to every Redis key this backend
            writes, to avoid collisions with unrelated keys in a shared
            Redis instance.
        **options: Accepted for interface compatibility; unused.
    """

    def __init__(
        self,
        *,
        url: str | None = None,
        client: Any | None = None,
        key_prefix: str = _DEFAULT_KEY_PREFIX,
        **options: Any,
    ) -> None:
        super().__init__(**options)
        self._client = (
            client
            if client is not None
            else redis_lib.Redis.from_url(url or "redis://localhost:6379/0")
        )
        self._prefix = key_prefix

    def _redis_key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def acquire_or_get(self, key: str, fingerprint: str, *, lock_ttl: timedelta) -> AcquireResult:
        """See :meth:`drf_idempotency.backends.base.BaseBackend.acquire_or_get`."""
        redis_key = self._redis_key(key)
        payload = self._encode(
            fingerprint=fingerprint,
            status="in_progress",
            response_status_code=None,
            response_headers=None,
            response_body=None,
        )
        acquired = self._client.set(redis_key, payload, nx=True, ex=int(lock_ttl.total_seconds()))
        if acquired:
            return AcquireResult(acquired=True, existing=None)
        raw = self._client.get(redis_key)
        if raw is None:
            # The record expired between our failed SETNX and this GET -
            # vanishingly rare, but safe to simply retry once.
            return self.acquire_or_get(key, fingerprint, lock_ttl=lock_ttl)
        return AcquireResult(acquired=False, existing=self._decode(key, raw))

    def complete(
        self,
        key: str,
        *,
        status_code: int,
        headers: Mapping[str, str],
        body: bytes,
        ttl: timedelta,
    ) -> None:
        """See :meth:`drf_idempotency.backends.base.BaseBackend.complete`."""
        redis_key = self._redis_key(key)
        existing = self._client.get(redis_key)
        fingerprint = json.loads(existing)["fingerprint"] if existing else ""
        payload = self._encode(
            fingerprint=fingerprint,
            status="completed",
            response_status_code=status_code,
            response_headers=dict(headers),
            response_body=base64.b64encode(body).decode("ascii"),
        )
        self._client.set(redis_key, payload, ex=int(ttl.total_seconds()))

    def fail(self, key: str) -> None:
        """See :meth:`drf_idempotency.backends.base.BaseBackend.fail`."""
        self._client.delete(self._redis_key(key))

    def get(self, key: str) -> StoredRecord | None:
        """See :meth:`drf_idempotency.backends.base.BaseBackend.get`."""
        raw = self._client.get(self._redis_key(key))
        if raw is None:
            return None
        return self._decode(key, raw)

    def cleanup_expired(self) -> int:
        """See :meth:`drf_idempotency.backends.base.BaseBackend.cleanup_expired`.

        Always returns ``0`` — Redis expires keys natively via ``EX``, so
        there is nothing for this method to do.
        """
        return 0

    def _encode(
        self,
        *,
        fingerprint: str,
        status: str,
        response_status_code: int | None,
        response_headers: Mapping[str, str] | None,
        response_body: str | None,
    ) -> str:
        return json.dumps(
            {
                "fingerprint": fingerprint,
                "status": status,
                "response_status_code": response_status_code,
                "response_headers": response_headers,
                "response_body": response_body,
                "created_at": timezone.now().isoformat(),
            }
        )

    def _decode(self, key: str, raw: bytes | str) -> StoredRecord:
        data = json.loads(raw)
        body = base64.b64decode(data["response_body"]) if data.get("response_body") else None
        return StoredRecord(
            key=key,
            fingerprint=data["fingerprint"],
            status=data["status"],
            response_status_code=data.get("response_status_code"),
            response_headers=data.get("response_headers"),
            response_body=body,
            created_at=datetime.fromisoformat(data["created_at"]),
        )
