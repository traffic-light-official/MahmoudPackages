"""Django app config for :mod:`drf_api_reverse`.

Registered only so the optional ``scaffold_api`` management command is
discoverable via ``INSTALLED_APPS`` - this package defines no models.
"""

from __future__ import annotations

from django.apps import AppConfig


class ApiReverseConfig(AppConfig):
    """App config for ``drf_api_reverse``."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_api_reverse"
    verbose_name = "DRF API Reverse"
