"""End-to-end tests hitting the real URL-routed DRF API."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import AbstractUser
from rest_framework.test import APIClient

from drf_notification.models import (
    Notification,
    NotificationPreference,
    NotificationSettings,
    WebhookTarget,
)
from drf_notification.unsubscribe import generate_unsubscribe_token

pytestmark = pytest.mark.django_db


class TestNotificationEndpoints:
    def test_list_only_returns_own_notifications(
        self,
        authenticated_client: APIClient,
        user: AbstractUser,
        other_user: AbstractUser,
    ) -> None:
        Notification.objects.create(recipient=user, event_key="e", channel="in_app")
        Notification.objects.create(recipient=other_user, event_key="e", channel="in_app")

        response = authenticated_client.get("/notifications/items/")

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_anonymous_request_is_rejected(self, api_client: APIClient) -> None:
        response = api_client.get("/notifications/items/")

        assert response.status_code in (401, 403)

    def test_mark_read_action(self, authenticated_client: APIClient, user: AbstractUser) -> None:
        notification = Notification.objects.create(recipient=user, event_key="e", channel="in_app")

        response = authenticated_client.post(f"/notifications/items/{notification.pk}/mark_read/")

        assert response.status_code == 200
        notification.refresh_from_db()
        assert notification.is_read is True

    def test_mark_all_read_action(
        self, authenticated_client: APIClient, user: AbstractUser
    ) -> None:
        Notification.objects.create(recipient=user, event_key="e1", channel="in_app")
        Notification.objects.create(recipient=user, event_key="e2", channel="in_app")

        response = authenticated_client.post("/notifications/items/mark-all-read/")

        assert response.status_code == 200
        assert response.data["marked_read"] == 2

    def test_cannot_mark_another_users_notification_read(
        self,
        authenticated_client: APIClient,
        other_user: AbstractUser,
    ) -> None:
        notification = Notification.objects.create(
            recipient=other_user, event_key="e", channel="in_app"
        )

        response = authenticated_client.post(f"/notifications/items/{notification.pk}/mark_read/")

        assert response.status_code == 404


class TestNotificationPreferenceEndpoints:
    def test_create_preference_is_scoped_to_requesting_user(
        self, authenticated_client: APIClient, user: AbstractUser
    ) -> None:
        response = authenticated_client.post(
            "/notifications/preferences/",
            {"event_key": "order.shipped", "channel": "email", "enabled": False},
        )

        assert response.status_code == 201
        preference = NotificationPreference.objects.get(pk=response.data["id"])
        assert preference.user_id == user.pk

    def test_list_only_returns_own_preferences(
        self, authenticated_client: APIClient, user: AbstractUser, other_user: AbstractUser
    ) -> None:
        NotificationPreference.objects.create(user=user, event_key="e", channel="email")
        NotificationPreference.objects.create(user=other_user, event_key="e", channel="email")

        response = authenticated_client.get("/notifications/preferences/")

        assert len(response.data) == 1


class TestWebhookTargetEndpoints:
    def test_create_rejects_unsafe_url(self, authenticated_client: APIClient) -> None:
        response = authenticated_client.post(
            "/notifications/webhook-targets/", {"url": "http://localhost/hook"}
        )

        assert response.status_code == 400

    def test_list_only_returns_own_targets(
        self, authenticated_client: APIClient, user: AbstractUser, other_user: AbstractUser
    ) -> None:
        WebhookTarget.objects.create(user=user, url="https://example.com/a")
        WebhookTarget.objects.create(user=other_user, url="https://example.com/b")

        response = authenticated_client.get("/notifications/webhook-targets/")

        assert len(response.data) == 1


class TestNotificationSettingsEndpoint:
    def test_get_creates_settings_on_first_access(
        self, authenticated_client: APIClient, user: AbstractUser
    ) -> None:
        response = authenticated_client.get("/notifications/settings/")

        assert response.status_code == 200
        assert NotificationSettings.objects.filter(user=user).exists()

    def test_patch_updates_settings(
        self, authenticated_client: APIClient, user: AbstractUser
    ) -> None:
        response = authenticated_client.patch(
            "/notifications/settings/", {"digest_frequency": "daily"}
        )

        assert response.status_code == 200
        assert response.data["digest_frequency"] == "daily"


class TestUnsubscribeEndpoint:
    def test_unsubscribe_from_everything(self, api_client: APIClient, user: AbstractUser) -> None:
        token = generate_unsubscribe_token(user.pk, None)

        response = api_client.post(f"/notifications/unsubscribe/{token}/")

        assert response.status_code == 200
        settings_obj = NotificationSettings.objects.get(user=user)
        assert settings_obj.unsubscribed_all is True

    def test_unsubscribe_from_one_event_disables_every_channel(
        self, api_client: APIClient, user: AbstractUser
    ) -> None:
        token = generate_unsubscribe_token(user.pk, "order.shipped")

        response = api_client.post(f"/notifications/unsubscribe/{token}/")

        assert response.status_code == 200
        preferences = NotificationPreference.objects.filter(user=user, event_key="order.shipped")
        assert preferences.exists()
        assert all(not p.enabled for p in preferences)

    def test_invalid_token_returns_400(self, api_client: APIClient) -> None:
        response = api_client.post("/notifications/unsubscribe/not-a-real-token/")

        assert response.status_code == 400

    def test_endpoint_requires_no_authentication(
        self, api_client: APIClient, user: AbstractUser
    ) -> None:
        token = generate_unsubscribe_token(user.pk, None)

        response = api_client.post(f"/notifications/unsubscribe/{token}/")

        assert response.status_code == 200


class TestPreferenceCenterEndpoint:
    def test_returns_settings_and_preferences_by_token(
        self, api_client: APIClient, user: AbstractUser
    ) -> None:
        settings_obj = NotificationSettings.objects.create(user=user)
        NotificationPreference.objects.create(user=user, event_key="e", channel="email")

        response = api_client.get(
            f"/notifications/preference-center/{settings_obj.unsubscribe_token}/"
        )

        assert response.status_code == 200
        assert len(response.data["preferences"]) == 1

    def test_invalid_token_returns_404(self, api_client: APIClient) -> None:
        response = api_client.get("/notifications/preference-center/not-a-real-token/")

        assert response.status_code == 404
