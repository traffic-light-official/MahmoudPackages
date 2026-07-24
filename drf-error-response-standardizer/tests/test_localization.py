"""Tests for :mod:`drf_error_response_standardizer.localization`."""

from __future__ import annotations

from django.utils import translation
from rest_framework.test import APIRequestFactory

from drf_error_response_standardizer.localization import (
    activate_for_request,
    resolve_language,
    translate,
)


class TestResolveLanguage:
    def test_defaults_to_language_code_setting_without_accept_language(
        self, api_rf: APIRequestFactory
    ) -> None:
        request = api_rf.get("/")

        assert resolve_language(request) == "en"

    def test_honors_accept_language_header(self, api_rf: APIRequestFactory) -> None:
        request = api_rf.get("/", HTTP_ACCEPT_LANGUAGE="fr")

        assert resolve_language(request) == "fr"


class TestActivateForRequest:
    def test_activates_the_resolved_language_for_the_duration_of_the_block(
        self, api_rf: APIRequestFactory
    ) -> None:
        request = api_rf.get("/", HTTP_ACCEPT_LANGUAGE="fr")

        with activate_for_request(request):
            assert translation.get_language() == "fr"

    def test_restores_the_previous_language_after_the_block(
        self, api_rf: APIRequestFactory
    ) -> None:
        request = api_rf.get("/", HTTP_ACCEPT_LANGUAGE="fr")

        with translation.override("en"):
            with activate_for_request(request):
                assert translation.get_language() == "fr"
            assert translation.get_language() == "en"


class TestTranslate:
    def test_returns_input_unchanged_when_no_translation_exists(self) -> None:
        with translation.override("en"):
            assert translate("Validation Error") == "Validation Error"
