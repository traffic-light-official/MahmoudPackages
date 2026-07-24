"""Pluggable storage backends for idempotency records.

See :mod:`drf_idempotency.backends.base` for the interface every backend
implements, and ``docs/architecture.md`` for how to write your own.
"""

from __future__ import annotations

from drf_idempotency.backends.base import AcquireResult, BaseBackend, StoredRecord

__all__ = ["AcquireResult", "BaseBackend", "StoredRecord"]
