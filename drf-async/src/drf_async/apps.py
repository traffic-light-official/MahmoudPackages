"""Django app config for :mod:`drf_async`.

Registered for consistency with this workspace's other packages - this
package defines no models and needs no app-loading side effects of its
own.
"""

from __future__ import annotations

from django.apps import AppConfig


class AsyncConfig(AppConfig):
    """App config for ``drf_async``."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_async"
    verbose_name = "DRF Async"
