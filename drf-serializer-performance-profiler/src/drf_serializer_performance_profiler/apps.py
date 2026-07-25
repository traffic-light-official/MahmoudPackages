"""Django app config for :mod:`drf_serializer_performance_profiler`.

Registered for consistency with this workspace's other packages - this
package defines no models and needs no app-loading side effects of its
own.
"""

from __future__ import annotations

from django.apps import AppConfig


class SerializerPerformanceProfilerConfig(AppConfig):
    """App config for ``drf_serializer_performance_profiler``."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_serializer_performance_profiler"
    verbose_name = "DRF Serializer Performance Profiler"
