"""Django app configuration."""

from __future__ import annotations

from django.apps import AppConfig


class DrfIdempotencyConfig(AppConfig):
    """App configuration for :mod:`drf_idempotency`.

    Must be listed in ``INSTALLED_APPS`` (and migrated) if you use the
    database backend, since it provides the
    :class:`~drf_idempotency.models.IdempotencyRecord` model. Not required
    if you use the Redis backend exclusively.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_idempotency"
    verbose_name = "DRF Idempotency"
