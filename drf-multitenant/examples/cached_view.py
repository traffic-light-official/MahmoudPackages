"""Example: per-tenant caching of an expensive computation.

See ``docs/examples.md``.
"""

from __future__ import annotations

from typing import Any

from drf_multitenant.cache import get_tenant_cache


def compute_stats() -> dict[str, Any]:
    """Placeholder for whatever expensive, tenant-scoped computation you have."""
    raise NotImplementedError("Replace with your own computation.")


def expensive_dashboard_stats() -> dict[str, Any]:
    cache = get_tenant_cache()
    stats: dict[str, Any] | None = cache.get("dashboard-stats")
    if stats is None:
        stats = compute_stats()  # scoped to the current tenant already
        cache.set("dashboard-stats", stats, timeout=300)
    return stats
