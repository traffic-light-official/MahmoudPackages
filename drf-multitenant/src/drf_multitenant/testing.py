"""Test-only helpers for exercising and verifying tenant isolation.

Not imported by anything else in this package — safe to depend on only
from your test suite (it's still shipped in the main package, not a
separate ``[test]`` extra, since it has no test-framework dependency of
its own beyond the standard library).
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from typing import Any

from django.db import models

from drf_multitenant.context import tenant_context
from drf_multitenant.exceptions import TenantLeakError
from drf_multitenant.managers import tenant_pk
from drf_multitenant.settings import get_setting

as_tenant = tenant_context
"""Alias for :func:`drf_multitenant.context.tenant_context`, for a test-reading name.

Example:
    >>> with as_tenant(some_tenant):
    ...     response = client.get("/api/articles/")
"""


@contextmanager
def as_no_tenant() -> Iterator[None]:
    """Explicitly clear the tenant context for the duration of the ``with`` block.

    Useful for asserting that tenant-scoped endpoints correctly reject
    or empty-out requests made with no resolvable tenant.
    """
    with tenant_context(None):
        yield


def assert_no_cross_tenant_leak(rows: Iterable[models.Model], expected_tenant: Any) -> None:
    """Assert every row in ``rows`` belongs to ``expected_tenant``.

    Args:
        rows: An iterable of tenant-scoped model instances (typically a
            queryset already evaluated, or a DRF response's parsed
            objects re-fetched as model instances).
        expected_tenant: The tenant every row is expected to belong to
            (an instance or a raw pk).

    Raises:
        drf_multitenant.exceptions.TenantLeakError: If any row's tenant
            field doesn't match ``expected_tenant``, naming the first
            offending row and its actual tenant id.
    """
    field = get_setting("TENANT_FIELD")
    expected_pk = tenant_pk(expected_tenant)
    for row in rows:
        actual = getattr(row, f"{field}_id", None)
        if actual != expected_pk:
            raise TenantLeakError(
                f"{type(row).__name__}(pk={row.pk!r}) belongs to tenant {actual!r}, "
                f"expected {expected_pk!r}."
            )
