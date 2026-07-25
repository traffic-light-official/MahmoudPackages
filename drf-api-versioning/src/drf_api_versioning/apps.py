"""Django app config for :mod:`drf_api_versioning`.

Registered so ``API_VERSIONING`` setting validation and the
``list_api_versions`` management command are wired up on app load -
this package defines no models.
"""

from __future__ import annotations

from django.apps import AppConfig


class ApiVersioningConfig(AppConfig):
    """App config for ``drf_api_versioning``."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_api_versioning"
    verbose_name = "DRF API Versioning"
