"""Tests for drf_file_pipeline.images."""

from __future__ import annotations

from pathlib import Path

import pytest
from django.test import override_settings
from PIL import Image

from drf_file_pipeline.images import (
    ImagePreset,
    generate_image_presets,
    get_configured_presets,
    preset_key,
    render_preset,
)
from drf_file_pipeline.models import FileUpload
from drf_file_pipeline.storage import S3StorageBackend

pytestmark = pytest.mark.django_db


class TestImagePreset:
    def test_valid_modes(self) -> None:
        for mode in ("cover", "contain", "crop"):
            ImagePreset(name="x", width=10, height=10, mode=mode)

    def test_invalid_mode_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown image preset mode"):
            ImagePreset(name="x", width=10, height=10, mode="stretch")


class TestGetConfiguredPresets:
    def test_empty_by_default(self) -> None:
        with override_settings(FILE_PIPELINE={"BUCKET_NAME": "b"}):
            assert get_configured_presets() == []

    def test_parses_configured_presets(self) -> None:
        with override_settings(
            FILE_PIPELINE={
                "BUCKET_NAME": "b",
                "IMAGE_PRESETS": {"thumb": {"width": 100, "height": 50, "mode": "contain"}},
            }
        ):
            presets = get_configured_presets()
        assert presets == [ImagePreset(name="thumb", width=100, height=50, mode="contain")]

    def test_mode_defaults_to_cover(self) -> None:
        with override_settings(
            FILE_PIPELINE={
                "BUCKET_NAME": "b",
                "IMAGE_PRESETS": {"thumb": {"width": 10, "height": 10}},
            }
        ):
            presets = get_configured_presets()
        assert presets[0].mode == "cover"


class TestPresetKey:
    def test_derives_key_with_suffix(self) -> None:
        preset = ImagePreset(name="thumb", width=10, height=10)
        assert preset_key("uploads/a/photo.png", preset) == "uploads/a/photo__thumb.png"


def _make_test_image(path: Path, size: tuple[int, int] = (400, 300), color: str = "red") -> None:
    Image.new("RGB", size, color=color).save(path, format="PNG")


class TestRenderPreset:
    def test_cover_mode_produces_exact_dimensions(self, tmp_path: Path) -> None:
        source = tmp_path / "source.png"
        dest = tmp_path / "dest.png"
        _make_test_image(source, size=(400, 300))

        render_preset(
            str(source), str(dest), ImagePreset(name="t", width=100, height=100, mode="cover")
        )

        with Image.open(dest) as result:
            assert result.size == (100, 100)

    def test_contain_mode_preserves_aspect_ratio_within_bounds(self, tmp_path: Path) -> None:
        source = tmp_path / "source.png"
        dest = tmp_path / "dest.png"
        _make_test_image(source, size=(400, 200))

        render_preset(
            str(source), str(dest), ImagePreset(name="t", width=100, height=100, mode="contain")
        )

        with Image.open(dest) as result:
            assert result.width <= 100
            assert result.height <= 100
            assert result.width == 100  # the wider dimension hits the bound first

    def test_crop_mode_takes_top_left(self, tmp_path: Path) -> None:
        source = tmp_path / "source.png"
        dest = tmp_path / "dest.png"
        _make_test_image(source, size=(400, 300))

        render_preset(
            str(source), str(dest), ImagePreset(name="t", width=50, height=50, mode="crop")
        )

        with Image.open(dest) as result:
            assert result.size == (50, 50)

    def test_jpeg_with_alpha_source_is_converted_to_rgb(self, tmp_path: Path) -> None:
        source = tmp_path / "source.jpg"
        dest = tmp_path / "dest.jpg"
        Image.new("RGB", (100, 100), color="blue").save(source, format="JPEG")

        render_preset(
            str(source), str(dest), ImagePreset(name="t", width=50, height=50, mode="cover")
        )

        with Image.open(dest) as result:
            assert result.mode == "RGB"
            assert result.format == "JPEG"


class TestGenerateImagePresets:
    def test_no_presets_configured_returns_empty(self, storage: S3StorageBackend) -> None:
        upload = FileUpload.objects.create(
            key="uploads/a/photo.png", original_filename="photo.png", content_type="image/png"
        )
        with override_settings(FILE_PIPELINE={"BUCKET_NAME": "test-bucket"}):
            assert generate_image_presets(upload, storage) == {}

    def test_generates_and_uploads_every_preset(
        self, storage: S3StorageBackend, tmp_path: Path
    ) -> None:
        source = tmp_path / "source.png"
        _make_test_image(source, size=(400, 300))
        upload = FileUpload.objects.create(
            key="uploads/a/photo.png", original_filename="photo.png", content_type="image/png"
        )
        storage.upload_from_path(key=upload.key, path=str(source), content_type="image/png")

        with override_settings(
            FILE_PIPELINE={
                "BUCKET_NAME": "test-bucket",
                "IMAGE_PRESETS": {
                    "thumb": {"width": 100, "height": 100, "mode": "cover"},
                    "medium": {"width": 200, "height": 200, "mode": "contain"},
                },
            }
        ):
            generated = generate_image_presets(upload, storage)

        assert set(generated) == {"thumb", "medium"}
        assert generated["thumb"] == "uploads/a/photo__thumb.png"
        thumb_info = storage.head(key=generated["thumb"])
        assert thumb_info is not None
