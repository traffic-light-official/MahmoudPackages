"""Django settings integration for :mod:`drf_file_pipeline`.

All configuration lives under a single Django setting, ``FILE_PIPELINE``,
a dictionary of overrides merged on top of :data:`DEFAULTS`. See
``docs/settings.md`` for the description of every key.
"""

from __future__ import annotations

from typing import Any, Final

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.signals import setting_changed
from django.utils.functional import cached_property

USER_SETTINGS_NAME: Final[str] = "FILE_PIPELINE"

DEFAULTS: Final[dict[str, Any]] = {
    #: Dotted path to the :class:`~drf_file_pipeline.storage.StorageBackend`
    #: implementation to use.
    "STORAGE_BACKEND": "drf_file_pipeline.storage.S3StorageBackend",
    #: S3 bucket uploads are written to. Required to use the built-in
    #: ``S3StorageBackend``.
    "BUCKET_NAME": None,
    #: AWS region for the S3 client. ``None`` defers to boto3's own
    #: region resolution (env var, config file, instance profile).
    "AWS_REGION": None,
    #: Key prefix applied to every object this package writes.
    "KEY_PREFIX": "uploads/",
    #: How long (seconds) presigned upload URLs remain valid.
    "PRESIGNED_UPLOAD_EXPIRY": 3600,
    #: How long (seconds) presigned download/GET URLs remain valid.
    "PRESIGNED_DOWNLOAD_EXPIRY": 300,
    #: Uploads at or above this size (bytes) use presigned multipart
    #: upload instead of a single presigned POST.
    "MULTIPART_THRESHOLD": 25 * 1024 * 1024,
    #: Size (bytes) of each multipart upload part, except the last.
    #: S3 requires at least 5 MiB for every part but the last.
    "MULTIPART_CHUNK_SIZE": 25 * 1024 * 1024,
    #: Hard cap (bytes) on any single upload. ``None`` disables the check.
    "MAX_UPLOAD_SIZE": None,
    #: Allowed MIME types. ``None`` disables the check (any type allowed).
    "ALLOWED_CONTENT_TYPES": None,
    #: Extra dotted paths to ``(upload) -> None`` callables, each
    #: raising :class:`~drf_file_pipeline.exceptions.ValidationFailedError`
    #: to reject an upload.
    "VALIDATION_CALLBACKS": (),
    #: Dotted path to a ``(upload) -> ScanResult`` callable. Defaults to
    #: a no-op scanner that always reports clean — see
    #: ``docs/security.md`` before relying on this in production.
    "VIRUS_SCAN_CALLBACK": "drf_file_pipeline.virus_scan.null_scanner",
    #: Named image presets generated for image uploads. Each value is a
    #: dict with ``width``, ``height``, and ``mode``
    #: (``"cover"``, ``"contain"``, or ``"crop"``).
    "IMAGE_PRESETS": {},
    #: MIME type prefix used to decide whether an upload is an image
    #: (and therefore eligible for preset generation).
    "IMAGE_CONTENT_TYPE_PREFIX": "image/",
    #: Age (hours) after which an upload stuck before ``COMPLETED``
    #: is considered abandoned by ``cleanup_abandoned_uploads``.
    "ABANDONED_UPLOAD_MAX_AGE_HOURS": 24,
}

_TYPE_CHECKS: Final[dict[str, type | tuple[type, ...]]] = {
    "STORAGE_BACKEND": str,
    "BUCKET_NAME": (str, type(None)),
    "AWS_REGION": (str, type(None)),
    "KEY_PREFIX": str,
    "PRESIGNED_UPLOAD_EXPIRY": int,
    "PRESIGNED_DOWNLOAD_EXPIRY": int,
    "MULTIPART_THRESHOLD": int,
    "MULTIPART_CHUNK_SIZE": int,
    "MAX_UPLOAD_SIZE": (int, type(None)),
    "ALLOWED_CONTENT_TYPES": (list, tuple, type(None)),
    "VALIDATION_CALLBACKS": (list, tuple),
    "VIRUS_SCAN_CALLBACK": str,
    "IMAGE_PRESETS": dict,
    "IMAGE_CONTENT_TYPE_PREFIX": str,
    "ABANDONED_UPLOAD_MAX_AGE_HOURS": int,
}


class _FilePipelineSettings:
    """Lazily-evaluated, validated, cache-invalidating settings object."""

    def __init__(self) -> None:
        setting_changed.connect(self._on_setting_changed)

    @cached_property
    def _user_settings(self) -> dict[str, Any]:
        raw = getattr(settings, USER_SETTINGS_NAME, {})
        if not isinstance(raw, dict):
            raise ImproperlyConfigured(
                f"The '{USER_SETTINGS_NAME}' Django setting must be a dict, "
                f"got {type(raw).__name__}."
            )
        unknown_keys = set(raw) - set(DEFAULTS)
        if unknown_keys:
            raise ImproperlyConfigured(
                f"Unknown key(s) in '{USER_SETTINGS_NAME}': {sorted(unknown_keys)}. "
                f"Valid keys are: {sorted(DEFAULTS)}."
            )
        merged = {**DEFAULTS, **raw}
        for key, expected_type in _TYPE_CHECKS.items():
            if not isinstance(merged[key], expected_type):
                raise ImproperlyConfigured(
                    f"'{USER_SETTINGS_NAME}[\"{key}\"]' must be of type "
                    f"{expected_type}, got {type(merged[key]).__name__}."
                )
        if merged["MULTIPART_CHUNK_SIZE"] < 5 * 1024 * 1024:
            raise ImproperlyConfigured(
                f"'{USER_SETTINGS_NAME}[\"MULTIPART_CHUNK_SIZE\"]' must be at least 5 MiB "
                f"(S3's minimum part size for all but the last part)."
            )
        return merged

    def __getitem__(self, key: str) -> Any:
        if key not in DEFAULTS:
            raise KeyError(f"Invalid setting: {key!r}. Valid keys are: {sorted(DEFAULTS)}.")
        return self._user_settings[key]

    def _on_setting_changed(self, *, sender: Any, setting: str, **kwargs: Any) -> None:
        if setting == USER_SETTINGS_NAME:
            self.__dict__.pop("_user_settings", None)


app_settings = _FilePipelineSettings()


def get_setting(key: str) -> Any:
    """Return the effective value of a single package setting.

    Args:
        key: One of the keys documented in :data:`DEFAULTS`.

    Returns:
        The user-configured value if present in the ``FILE_PIPELINE``
        Django setting, otherwise the default.

    Raises:
        KeyError: If ``key`` is not a recognized setting name.
        django.core.exceptions.ImproperlyConfigured: If the
            ``FILE_PIPELINE`` setting is malformed.
    """
    return app_settings[key]
