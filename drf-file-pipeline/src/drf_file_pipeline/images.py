"""Image preset / thumbnail generation via Pillow.

Presets are configured in ``FILE_PIPELINE["IMAGE_PRESETS"]`` — a dict of
``name -> {"width": int, "height": int, "mode": "cover" | "contain" | "crop"}``.
:func:`generate_image_presets` downloads the original, renders every
configured preset, and uploads each back to the store under a derived
key, returning ``{preset_name: key}`` for the caller (typically
:mod:`drf_file_pipeline.processing`) to persist onto the upload record.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from PIL import Image, ImageOps

from drf_file_pipeline.models import FileUpload
from drf_file_pipeline.settings import get_setting
from drf_file_pipeline.storage import StorageBackend

_VALID_MODES = frozenset({"cover", "contain", "crop"})


@dataclass(frozen=True, slots=True)
class ImagePreset:
    """A single named image preset.

    Attributes:
        name: The preset's name, used in the derived object key.
        width: Target width in pixels.
        height: Target height in pixels.
        mode: ``"cover"`` (fill and crop to exactly fit), ``"contain"``
            (fit within, preserving aspect ratio, no cropping), or
            ``"crop"`` (a hard top-left crop, no resizing).
    """

    name: str
    width: int
    height: int
    mode: str = "cover"

    def __post_init__(self) -> None:
        if self.mode not in _VALID_MODES:
            raise ValueError(
                f"Unknown image preset mode: {self.mode!r}. Valid: {sorted(_VALID_MODES)}"
            )


def get_configured_presets() -> list[ImagePreset]:
    """Parse ``FILE_PIPELINE["IMAGE_PRESETS"]`` into a list of :class:`ImagePreset`."""
    raw: dict[str, dict[str, Any]] = get_setting("IMAGE_PRESETS")
    presets = []
    for name, config in raw.items():
        presets.append(
            ImagePreset(
                name=name,
                width=int(config["width"]),
                height=int(config["height"]),
                mode=str(config.get("mode", "cover")),
            )
        )
    return presets


def preset_key(original_key: str, preset: ImagePreset) -> str:
    """Derive the storage key for a preset from the original upload's key."""
    # Storage keys always use forward slashes regardless of platform —
    # PurePosixPath (not Path) keeps that true even when this runs on
    # Windows, where a plain Path would normalize to backslashes.
    key = PurePosixPath(original_key)
    return f"{key.with_suffix('')}__{preset.name}{key.suffix}"


def render_preset(source_path: str, dest_path: str, preset: ImagePreset) -> None:
    """Render one preset from the image at ``source_path`` into ``dest_path``."""
    with Image.open(source_path) as source:
        # Captured before exif_transpose(): it returns a freshly
        # transformed Image object which does not carry over the
        # `.format` attribute (only images loaded via Image.open() have
        # one), so reading it afterwards would always be None.
        image_format = source.format or "PNG"
        upright = ImageOps.exif_transpose(source) or source
        if preset.mode == "cover":
            rendered = ImageOps.fit(
                upright, (preset.width, preset.height), Image.Resampling.LANCZOS
            )
        elif preset.mode == "contain":
            rendered = upright.copy()
            rendered.thumbnail((preset.width, preset.height), Image.Resampling.LANCZOS)
        else:  # crop
            box = (0, 0, min(preset.width, upright.width), min(preset.height, upright.height))
            rendered = upright.crop(box)
        if image_format == "JPEG" and rendered.mode in ("RGBA", "P"):
            rendered = rendered.convert("RGB")
        rendered.save(dest_path, format=image_format)


def generate_image_presets(upload: FileUpload, storage: StorageBackend) -> dict[str, str]:
    """Generate and upload every configured preset for ``upload``.

    Args:
        upload: The (image) upload to generate presets for.
        storage: The storage backend to download the original from and
            upload each generated preset to.

    Returns:
        ``{preset_name: storage_key}`` for every configured preset. Empty
        if no presets are configured.
    """
    presets = get_configured_presets()
    if not presets:
        return {}

    generated: dict[str, str] = {}
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_dir = Path(tmpdir)
        source_path = tmp_dir / "source"
        storage.download_to_path(key=upload.key, path=str(source_path))
        for preset in presets:
            dest_path = tmp_dir / preset.name
            render_preset(str(source_path), str(dest_path), preset)
            key = preset_key(upload.key, preset)
            storage.upload_from_path(key=key, path=str(dest_path), content_type=upload.content_type)
            generated[preset.name] = key
    return generated
