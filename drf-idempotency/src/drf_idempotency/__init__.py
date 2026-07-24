"""Stripe-style idempotency keys for Django REST Framework.

The public API is intentionally small:

* :class:`~drf_idempotency.middleware.IdempotencyMiddleware` — project-wide
  handling via ``MIDDLEWARE``.
* :func:`~drf_idempotency.decorators.idempotent` — per-view opt-in.
* :func:`~drf_idempotency.status.get_idempotency_status` — status
  tracking for a given key.
* :class:`~drf_idempotency.backends.base.BaseBackend` — the interface to
  implement for a custom storage backend.

See ``docs/quickstart.md`` for a complete end-to-end example.
"""

from __future__ import annotations

from drf_idempotency.backends.base import AcquireResult, BaseBackend, StoredRecord
from drf_idempotency.decorators import idempotent
from drf_idempotency.exceptions import (
    ConcurrentRequestError,
    IdempotencyError,
    IdempotencyKeyReuseError,
    InvalidIdempotencyKeyError,
    MissingIdempotencyKeyError,
)
from drf_idempotency.fingerprint import compute_fingerprint
from drf_idempotency.middleware import IdempotencyMiddleware
from drf_idempotency.status import get_idempotency_status

__version__ = "1.0.0"

__all__ = [
    "AcquireResult",
    "BaseBackend",
    "ConcurrentRequestError",
    "IdempotencyError",
    "IdempotencyKeyReuseError",
    "IdempotencyMiddleware",
    "InvalidIdempotencyKeyError",
    "MissingIdempotencyKeyError",
    "StoredRecord",
    "__version__",
    "compute_fingerprint",
    "get_idempotency_status",
    "idempotent",
]
