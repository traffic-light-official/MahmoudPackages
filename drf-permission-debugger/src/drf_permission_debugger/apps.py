"""Django app config for :mod:`drf_permission_debugger`.

Registered for consistency with this workspace's other packages, and
required for Django to discover the ``show_view_permissions``
management command - this package defines no models and needs no
app-loading side effects of its own.
"""

from __future__ import annotations

from django.apps import AppConfig


class PermissionDebuggerConfig(AppConfig):
    """App config for ``drf_permission_debugger``."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_permission_debugger"
    verbose_name = "DRF Permission Debugger"
