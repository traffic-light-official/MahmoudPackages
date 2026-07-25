"""End-to-end tests: real HTTP requests through the router."""

from __future__ import annotations

import pytest
from django.test import override_settings

pytestmark = pytest.mark.django_db


class TestBehaviorIsUnchanged:
    """The mixin must never change who is authorized to do what."""

    def test_granted_request_still_succeeds(self, api_client) -> None:
        response = api_client.get("/ping/")
        assert response.status_code == 200
        assert response.json() == {"pong": True}

    def test_denied_request_still_returns_403(self, api_client, make_user) -> None:
        user = make_user()
        api_client.force_authenticate(user=user)
        response = api_client.get("/multi-denied/")
        assert response.status_code == 403
        assert response.json()["detail"] == "Denied by DenyAll."

    def test_unauthenticated_request_still_returns_403(self, api_client) -> None:
        response = api_client.get("/multi-denied/")
        assert response.status_code == 403


class TestTraceHeaderDisabledByDefault:
    def test_no_header_when_permission_debugger_disabled(self, api_client) -> None:
        response = api_client.get("/ping/")
        assert "X-Permission-Trace" not in response.headers


class TestTraceHeaderEnabled:
    def test_staff_user_sees_the_trace_header(self, api_client, make_user) -> None:
        staff = make_user(is_staff=True)
        api_client.force_authenticate(user=staff)
        with override_settings(PERMISSION_DEBUGGER={"ENABLED": True}):
            response = api_client.get("/multi-denied/")
        assert response.status_code == 403
        assert response.headers["X-Permission-Trace"] == "IsAuthenticated=granted, DenyAll=denied"

    def test_non_staff_user_does_not_see_the_trace_header_by_default(
        self, api_client, make_user
    ) -> None:
        user = make_user(is_staff=False)
        api_client.force_authenticate(user=user)
        with override_settings(PERMISSION_DEBUGGER={"ENABLED": True}):
            response = api_client.get("/multi-denied/")
        assert response.status_code == 403
        assert "X-Permission-Trace" not in response.headers

    def test_anonymous_user_does_not_see_the_trace_header_by_default(self, api_client) -> None:
        with override_settings(PERMISSION_DEBUGGER={"ENABLED": True}):
            response = api_client.get("/multi-denied/")
        assert "X-Permission-Trace" not in response.headers

    def test_restrict_to_staff_false_shows_it_to_everyone(self, api_client) -> None:
        with override_settings(PERMISSION_DEBUGGER={"ENABLED": True, "RESTRICT_TO_STAFF": False}):
            response = api_client.get("/multi-denied/")
        assert response.headers["X-Permission-Trace"] == "IsAuthenticated=denied"

    def test_custom_header_name(self, api_client, make_user) -> None:
        staff = make_user(is_staff=True)
        api_client.force_authenticate(user=staff)
        with override_settings(
            PERMISSION_DEBUGGER={"ENABLED": True, "HEADER_NAME": "X-Debug-Perms"}
        ):
            response = api_client.get("/ping/")
        assert response.headers["X-Debug-Perms"] == "AllowAny=granted"

    def test_granted_request_trace_shows_a_single_granted_entry(
        self, api_client, make_user
    ) -> None:
        staff = make_user(is_staff=True)
        api_client.force_authenticate(user=staff)
        with override_settings(PERMISSION_DEBUGGER={"ENABLED": True}):
            response = api_client.get("/ping/")
        assert response.headers["X-Permission-Trace"] == "AllowAny=granted"


class TestResponseBodyTrace:
    def test_included_when_configured_and_denied(self, api_client, make_user) -> None:
        staff = make_user(is_staff=True)
        api_client.force_authenticate(user=staff)
        with override_settings(
            PERMISSION_DEBUGGER={"ENABLED": True, "INCLUDE_IN_RESPONSE_BODY": True}
        ):
            response = api_client.get("/multi-denied/")
        body = response.json()
        assert "permission_trace" in body
        assert body["permission_trace"] == [
            {
                "permission_class": "IsAuthenticated",
                "granted": True,
                "object_level": False,
                "message": None,
                "code": None,
            },
            {
                "permission_class": "DenyAll",
                "granted": False,
                "object_level": False,
                "message": "Denied by DenyAll.",
                "code": "deny_all",
            },
        ]

    def test_not_included_when_request_is_granted(self, api_client, make_user) -> None:
        staff = make_user(is_staff=True)
        api_client.force_authenticate(user=staff)
        with override_settings(
            PERMISSION_DEBUGGER={"ENABLED": True, "INCLUDE_IN_RESPONSE_BODY": True}
        ):
            response = api_client.get("/ping/")
        assert "permission_trace" not in response.json()

    def test_not_included_when_setting_is_off(self, api_client, make_user) -> None:
        staff = make_user(is_staff=True)
        api_client.force_authenticate(user=staff)
        with override_settings(
            PERMISSION_DEBUGGER={"ENABLED": True, "INCLUDE_IN_RESPONSE_BODY": False}
        ):
            response = api_client.get("/multi-denied/")
        assert "permission_trace" not in response.json()


class TestObjectLevelPermissionTrace:
    def test_object_level_check_is_recorded_alongside_request_level(
        self, api_client, make_article, make_user
    ) -> None:
        # ArticleViewSet.permission_classes = [IsAuthenticated, IsOwner].
        # Neither denies at the request level (IsOwner has no
        # has_permission override, so it inherits BasePermission's
        # always-grant default) - both request-level checks are recorded
        # as granted, then check_object_permissions() runs the same two
        # classes again against the actual object, where IsOwner's
        # has_object_permission override denies a non-owner.
        owner = make_user()
        other_user = make_user(is_staff=True)
        article = make_article(owner=owner)
        api_client.force_authenticate(user=other_user)

        with override_settings(PERMISSION_DEBUGGER={"ENABLED": True}):
            response = api_client.get(f"/articles/{article.pk}/")

        assert response.status_code == 403
        trace_header = response.headers["X-Permission-Trace"]
        assert trace_header == (
            "IsAuthenticated=granted, IsOwner=granted, IsAuthenticated=granted, IsOwner=denied"
        )

    def test_owner_can_retrieve_their_own_article(
        self, api_client, make_article, make_user
    ) -> None:
        owner = make_user()
        article = make_article(owner=owner)
        api_client.force_authenticate(user=owner)

        response = api_client.get(f"/articles/{article.pk}/")
        assert response.status_code == 200
