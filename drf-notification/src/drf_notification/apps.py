"""Django app configuration for :mod:`drf_notification`."""

from __future__ import annotations

from django.apps import AppConfig


class NotificationConfig(AppConfig):
    """Registers this package as a Django app.

    Add ``"drf_notification"`` to ``INSTALLED_APPS`` to enable its models,
    admin registration, management commands, and (if Celery is
    installed) task autodiscovery.
    """

    name = "drf_notification"
    verbose_name = "Notifications"
    default_auto_field = "django.db.models.BigAutoField"
