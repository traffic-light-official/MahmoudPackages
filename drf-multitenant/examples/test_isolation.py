"""Example: asserting tenant isolation in your own test suite.

See ``docs/examples.md`` and ``docs/testing.md``. Illustrative only —
not collected by this package's own pytest run (it isn't named
``test_*.py`` from ``tests/``, and references a project structure —
``tenant_a``/``tenant_b`` fixtures, ``examples.minimal_app`` — that
isn't part of this package's installed test app).
"""

from __future__ import annotations

import pytest
from examples.minimal_app.models import Project, Tenant

from drf_multitenant.testing import as_tenant, assert_no_cross_tenant_leak


@pytest.mark.django_db
def test_projects_are_isolated(tenant_a: Tenant, tenant_b: Tenant) -> None:
    with as_tenant(tenant_a):
        Project.objects.create(name="A's project")
    with as_tenant(tenant_b):
        Project.objects.create(name="B's project")

    with as_tenant(tenant_a):
        rows = list(Project.objects.all())
    assert len(rows) == 1
    assert_no_cross_tenant_leak(rows, tenant_a)
