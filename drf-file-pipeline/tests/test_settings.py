"""Tests for drf_file_pipeline.settings."""

from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from drf_file_pipeline.settings import get_setting


class TestDefaults:
    def test_bucket_name_is_configured_by_test_settings(self) -> None:
        assert get_setting("BUCKET_NAME") == "test-bucket"

    def test_key_prefix_default(self) -> None:
        with override_settings(FILE_PIPELINE={"BUCKET_NAME": "b"}):
            assert get_setting("KEY_PREFIX") == "uploads/"

    def test_virus_scan_callback_default(self) -> None:
        with override_settings(FILE_PIPELINE={"BUCKET_NAME": "b"}):
            assert get_setting("VIRUS_SCAN_CALLBACK") == "drf_file_pipeline.virus_scan.null_scanner"

    def test_image_presets_default_empty(self) -> None:
        with override_settings(FILE_PIPELINE={"BUCKET_NAME": "b"}):
            assert get_setting("IMAGE_PRESETS") == {}

    def test_invalid_key_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            get_setting("NOT_A_REAL_SETTING")


class TestOverrides:
    def test_override_is_picked_up(self) -> None:
        with override_settings(FILE_PIPELINE={"BUCKET_NAME": "b", "KEY_PREFIX": "media/"}):
            assert get_setting("KEY_PREFIX") == "media/"
        assert get_setting("KEY_PREFIX") == "uploads/"

    def test_non_dict_setting_raises(self) -> None:
        with (
            override_settings(FILE_PIPELINE="not-a-dict"),
            pytest.raises(ImproperlyConfigured, match="must be a dict"),
        ):
            get_setting("KEY_PREFIX")

    def test_unknown_key_raises(self) -> None:
        with (
            override_settings(FILE_PIPELINE={"NOT_REAL": 1}),
            pytest.raises(ImproperlyConfigured, match="Unknown key"),
        ):
            get_setting("KEY_PREFIX")

    def test_wrong_type_raises(self) -> None:
        with (
            override_settings(FILE_PIPELINE={"BUCKET_NAME": "b", "MAX_UPLOAD_SIZE": "big"}),
            pytest.raises(ImproperlyConfigured, match="must be of type"),
        ):
            get_setting("MAX_UPLOAD_SIZE")

    def test_multipart_chunk_size_below_minimum_raises(self) -> None:
        with (
            override_settings(FILE_PIPELINE={"BUCKET_NAME": "b", "MULTIPART_CHUNK_SIZE": 100}),
            pytest.raises(ImproperlyConfigured, match="at least 5 MiB"),
        ):
            get_setting("MULTIPART_CHUNK_SIZE")
