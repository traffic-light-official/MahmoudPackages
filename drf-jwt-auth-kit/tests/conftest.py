"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from rest_framework.test import APIClient, APIRequestFactory

from drf_jwt_auth_kit.models import Device


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
        username="ada", email="ada@example.com", password="s3cret-password"
    )


@pytest.fixture
def other_user(db: None) -> AbstractUser:
    user_model = get_user_model()
    return user_model.objects.create_user(
        username="grace", email="grace@example.com", password="s3cret-password"
    )


@pytest.fixture
def device(db: None, user: AbstractUser) -> Device:
    return Device.objects.create(user=user, label="Test Device")


@pytest.fixture
def authenticated_client(api_client: APIClient, user: AbstractUser) -> APIClient:
    api_client.force_authenticate(user=user)
    return api_client
