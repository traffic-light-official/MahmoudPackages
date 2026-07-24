"""Django app configuration for :mod:`drf_error_response_standardizer`."""

from __future__ import annotations

from django.apps import AppConfig


class ErrorResponseStandardizerConfig(AppConfig):
    """Registers this package as a Django app.

    Add ``"drf_error_response_standardizer"`` to ``INSTALLED_APPS`` to make
    the ``generate_error_catalog`` management command discoverable.
    Everything else in this package (the exception handler, middleware,
    registry, normalization) works without installing the app.
    """

    name = "drf_error_response_standardizer"
    verbose_name = "DRF Error Response Standardizer"
    default_auto_field = "django.db.models.BigAutoField"
