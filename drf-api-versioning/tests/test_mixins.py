"""Tests for :mod:`drf_api_versioning.mixins`."""

from __future__ import annotations

from rest_framework.test import APIClient


class TestDeprecationHeaderMixin:
    def test_no_headers_for_a_fully_supported_version(self, api_client: APIClient) -> None:
        response = api_client.get("/v3/url-ping/")
        assert "Deprecation" not in response
        assert "Sunset" not in response
        assert "Link" not in response

    def test_deprecation_header_for_a_deprecated_version(self, api_client: APIClient) -> None:
        response = api_client.get("/v2/url-ping/")
        assert response["Deprecation"] == "Wed, 01 Jan 2020 00:00:00 GMT"

    def test_no_sunset_header_when_no_sunset_date_configured(self, api_client: APIClient) -> None:
        response = api_client.get("/v2/url-ping/")
        assert "Sunset" not in response

    def test_no_link_header_when_no_deprecation_link_configured(
        self, api_client: APIClient
    ) -> None:
        response = api_client.get("/v2/url-ping/")
        assert "Link" not in response

    def test_allow_sunset_response_includes_all_three_headers(
        self, api_client: APIClient, settings
    ) -> None:
        settings.API_VERSIONING = {**settings.API_VERSIONING, "ALLOW_SUNSET": True}
        response = api_client.get("/v1/url-ping/")

        assert response["Deprecation"] == "Wed, 01 Jan 2020 00:00:00 GMT"
        assert response["Sunset"] == "Mon, 01 Jun 2020 00:00:00 GMT"
        assert response["Link"] == '<https://example.com/docs/migrating-to-v3>; rel="deprecation"'

    def test_custom_header_names_are_respected(self, api_client: APIClient, settings) -> None:
        settings.API_VERSIONING = {
            **settings.API_VERSIONING,
            "DEPRECATION_HEADER": "X-Deprecated",
        }
        response = api_client.get("/v2/url-ping/")
        assert response["X-Deprecated"] == "Wed, 01 Jan 2020 00:00:00 GMT"
        assert "Deprecation" not in response
