"""Tests for :mod:`drf_api_versioning.versioning`, via real HTTP requests.

Exercises every registry-aware scheme through the actual DRF request
cycle (``tests.test_app``'s views/urls) rather than constructing
``Request``/``resolver_match`` objects by hand - this is what actually
validates the ``allowed_versions``/``default_version`` property
overrides and the ``super().determine_version()`` interaction with each
real DRF base class.
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.test import APIClient

from drf_api_versioning.signals import deprecated_version_used


class TestURLPathVersioning:
    def test_known_version_resolves(self, api_client: APIClient) -> None:
        response = api_client.get("/v3/url-ping/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["version"] == "v3"

    def test_unknown_version_is_404_with_supported_list(self, api_client: APIClient) -> None:
        response = api_client.get("/v9/url-ping/")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "v9" in str(response.data)
        assert "v3" in str(response.data)

    def test_sunset_version_is_410(self, api_client: APIClient) -> None:
        response = api_client.get("/v1/url-ping/")
        assert response.status_code == status.HTTP_410_GONE

    def test_deprecated_but_not_sunset_version_succeeds(self, api_client: APIClient) -> None:
        response = api_client.get("/v2/url-ping/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["version"] == "v2"


class TestNamespaceVersioning:
    def test_known_version_resolves(self, api_client: APIClient) -> None:
        response = api_client.get("/v3/ns-ping/ping/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["version"] == "v3"

    def test_unknown_version_is_404(self, api_client: APIClient) -> None:
        response = api_client.get("/v9/ns-ping/ping/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_sunset_version_is_410(self, api_client: APIClient) -> None:
        response = api_client.get("/v1/ns-ping/ping/")
        assert response.status_code == status.HTTP_410_GONE


class TestAcceptHeaderVersioning:
    def test_known_version_resolves(self, api_client: APIClient) -> None:
        response = api_client.get("/accept-ping/", HTTP_ACCEPT="application/json; version=v3")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["version"] == "v3"

    def test_no_version_uses_default(self, api_client: APIClient) -> None:
        response = api_client.get("/accept-ping/", HTTP_ACCEPT="application/json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["version"] == "v3"

    def test_unknown_version_is_406_matching_drf_s_native_status(
        self, api_client: APIClient
    ) -> None:
        # Accept-header version mismatches are a content-negotiation failure,
        # so this preserves DRF's own NotAcceptable (406) - only the message
        # is richer (names the version and lists what's supported).
        response = api_client.get("/accept-ping/", HTTP_ACCEPT="application/json; version=v9")
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
        assert "v9" in str(response.data)
        assert "v3" in str(response.data)

    def test_sunset_version_is_410(self, api_client: APIClient) -> None:
        response = api_client.get("/accept-ping/", HTTP_ACCEPT="application/json; version=v1")
        assert response.status_code == status.HTTP_410_GONE


class TestQueryParameterVersioning:
    def test_known_version_resolves(self, api_client: APIClient) -> None:
        response = api_client.get("/query-ping/?version=v3")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["version"] == "v3"

    def test_no_version_uses_default(self, api_client: APIClient) -> None:
        response = api_client.get("/query-ping/")
        assert response.data["version"] == "v3"

    def test_unknown_version_is_404(self, api_client: APIClient) -> None:
        response = api_client.get("/query-ping/?version=v9")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_sunset_version_is_410(self, api_client: APIClient) -> None:
        response = api_client.get("/query-ping/?version=v1")
        assert response.status_code == status.HTTP_410_GONE


class TestHostNameVersioning:
    def test_known_version_resolves(self, api_client: APIClient) -> None:
        response = api_client.get("/host-ping/", HTTP_HOST="v3.example.com")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["version"] == "v3"

    def test_non_matching_hostname_uses_default(self, api_client: APIClient) -> None:
        response = api_client.get("/host-ping/", HTTP_HOST="testserver")
        assert response.data["version"] == "v3"

    def test_unknown_version_is_404(self, api_client: APIClient) -> None:
        response = api_client.get("/host-ping/", HTTP_HOST="v9.example.com")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_sunset_version_is_410(self, api_client: APIClient) -> None:
        response = api_client.get("/host-ping/", HTTP_HOST="v1.example.com")
        assert response.status_code == status.HTTP_410_GONE


class TestDeprecatedVersionSignal:
    def test_signal_fires_for_a_deprecated_but_not_sunset_version(
        self, api_client: APIClient
    ) -> None:
        received = []

        def handler(sender: object, **kwargs: object) -> None:
            received.append(kwargs)

        deprecated_version_used.connect(handler)
        try:
            api_client.get("/v2/url-ping/")
        finally:
            deprecated_version_used.disconnect(handler)

        assert len(received) == 1
        assert received[0]["version"] == "v2"
        assert received[0]["version_info"].name == "v2"

    def test_signal_does_not_fire_for_a_supported_version(self, api_client: APIClient) -> None:
        received = []

        def handler(sender: object, **kwargs: object) -> None:
            received.append(kwargs)

        deprecated_version_used.connect(handler)
        try:
            api_client.get("/v3/url-ping/")
        finally:
            deprecated_version_used.disconnect(handler)

        assert received == []


class TestNoVersionResolvedAndNoDefault:
    def test_unnamespaced_request_is_permitted_when_no_default_is_configured(
        self, api_client: APIClient, settings
    ) -> None:
        # NamespaceVersioning is the one scheme that returns
        # ``default_version`` directly, without validating it, when no
        # namespace matches - see the comment in
        # ``_RegistryVersioningMixin.determine_version``. Every other
        # scheme instead rejects an unresolvable version outright, since
        # our ``allowed_versions`` is always non-empty.
        settings.API_VERSIONING = {**settings.API_VERSIONING, "DEFAULT_VERSION": None}
        response = api_client.get("/plain-ns-ping/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["version"] is None


class TestAllowSunsetOverride:
    def test_sunset_version_succeeds_when_allowed(self, api_client: APIClient, settings) -> None:
        settings.API_VERSIONING = {
            **settings.API_VERSIONING,
            "ALLOW_SUNSET": True,
        }
        response = api_client.get("/v1/url-ping/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["version"] == "v1"
