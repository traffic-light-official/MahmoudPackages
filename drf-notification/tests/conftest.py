"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.cache import cache
from rest_framework.test import APIClient, APIRequestFactory


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    # The rate limiter (drf_notification.ratelimit) is backed by Django's
    # cache framework, which - unlike the database - is not automatically
    # reset between tests. Without this, one test's rate-limit counters
    # leak into the next test that happens to use the same user/channel.
    cache.clear()


@pytest.fixture
def api_rf() -> APIRequestFactory:
    return APIRequestFactory()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db: None) -> AbstractUser:
    user_model = get_user_model()
    return user_model.objects.create_user(
        username="ada", email="ada@example.com", password="not-a-real-password"
    )


@pytest.fixture
def other_user(db: None) -> AbstractUser:
    user_model = get_user_model()
    return user_model.objects.create_user(
        username="grace", email="grace@example.com", password="not-a-real-password"
    )


@pytest.fixture
def authenticated_client(api_client: APIClient, user: AbstractUser) -> APIClient:
    api_client.force_authenticate(user=user)
    return api_client
