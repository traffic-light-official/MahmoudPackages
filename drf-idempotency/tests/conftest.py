"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from drf_idempotency.core import _reset_backend


@pytest.fixture(autouse=True)
def _reset_backend_singleton() -> None:
    """Force a fresh backend instance for every test.

    Backends are cached process-wide for performance (see
    ``drf_idempotency.core.get_backend``); tests that override
    ``IDEMPOTENCY`` settings need a fresh instance to pick up backend
    class/option changes, and fakeredis-backed tests need isolated state
    per test.
    """
    _reset_backend(sender=None, setting="IDEMPOTENCY")
    yield
    _reset_backend(sender=None, setting="IDEMPOTENCY")


@pytest.fixture
def client() -> APIClient:
    return APIClient()
