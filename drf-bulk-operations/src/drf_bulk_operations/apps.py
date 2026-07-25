"""Django app config for :mod:`drf_bulk_operations`.

Registered for consistency with this workspace's other packages - this
package defines no models and needs no app-loading side effects of its
own.
"""

from __future__ import annotations

from django.apps import AppConfig


class BulkOperationsConfig(AppConfig):
    """App config for ``drf_bulk_operations``."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_bulk_operations"
    verbose_name = "DRF Bulk Operations"
