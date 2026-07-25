"""Django app configuration for :mod:`drf_jwt_auth_kit`."""

from __future__ import annotations

from django.apps import AppConfig


class JWTAuthKitConfig(AppConfig):
    """Registers this package as a Django app.

    Add ``"drf_jwt_auth_kit"`` to ``INSTALLED_APPS`` to enable its
    models, admin registration, and management commands.
    """

    name = "drf_jwt_auth_kit"
    verbose_name = "JWT Auth Kit"
    default_auto_field = "django.db.models.BigAutoField"
