"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient, APIRequestFactory

from tests.test_app.models import Author


@pytest.fixture
def api_rf() -> APIRequestFactory:
    return APIRequestFactory()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def author(db: None) -> Author:
    return Author.objects.create(name="Ada Lovelace", email="ada@example.com")
