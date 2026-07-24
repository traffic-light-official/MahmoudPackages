"""Request fingerprinting.

A fingerprint is a stable hash of everything about a request that should
be identical across legitimate retries: its HTTP method, path, and body.
If a client reuses an idempotency key with a request whose fingerprint
differs from the one originally associated with that key, that's either a
client bug (accidentally reusing a key) or an attempt to get one key's
cached response applied to a different operation — either way, it's
rejected rather than silently replayed against the wrong request.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.http import HttpRequest


def compute_fingerprint(request: HttpRequest) -> str:
    """Compute a stable fingerprint of a request's method, path, and body.

    Args:
        request: The incoming request. ``request.body`` is read (and, per
            Django's own caching, becomes safe to read again later in the
            request/response cycle — e.g. by DRF's parsers).

    Returns:
        A 64-character SHA-256 hex digest.
    """
    hasher = hashlib.sha256()
    hasher.update(request.method.encode("utf-8") if request.method else b"")
    hasher.update(b"\n")
    hasher.update(request.path.encode("utf-8"))
    hasher.update(b"\n")
    hasher.update(request.body)
    return hasher.hexdigest()
