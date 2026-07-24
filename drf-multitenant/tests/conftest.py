"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from tests.test_app.models import Tenant


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def tenant_a(db: None) -> Tenant:
    return Tenant.objects.create(name="Acme", slug="acme")


@pytest.fixture
def tenant_b(db: None) -> Tenant:
    return Tenant.objects.create(name="Globex", slug="globex")
