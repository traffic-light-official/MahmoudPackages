"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

from typing import Any

import fakeredis
import pytest
from django.contrib.auth.models import AnonymousUser, User
from rest_framework.test import APIClient, APIRequestFactory

from drf_ratelimit_plus.client import set_redis_client


@pytest.fixture(autouse=True)
def _fake_redis() -> Any:
    """Give every test a fresh, isolated fakeredis instance.

    Test views' ``throttle_classes`` don't pass an explicit ``client=``,
    so they resolve one via ``get_redis_client()`` at check time - this
    fixture makes that resolution return a clean fakeredis instance for
    each test, so tests never see state left over from a previous one.
    """
    client = fakeredis.FakeRedis()
    set_redis_client(client)
    yield client
    set_redis_client(None)


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def api_rf() -> APIRequestFactory:
    return APIRequestFactory()


@pytest.fixture
def user(db: None) -> User:
    return User.objects.create_user(username="alice", password="password123")


@pytest.fixture
def anonymous_user() -> AnonymousUser:
    return AnonymousUser()
