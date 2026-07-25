"""Django app config for :mod:`drf_n_plus_one_query_guard`.

Registered so ``N_PLUS_ONE_GUARD`` setting validation and
``setting_changed`` signal handling are wired up on app load - this
package defines no models.
"""

from __future__ import annotations

from django.apps import AppConfig


class NPlusOneQueryGuardConfig(AppConfig):
    """App config for ``drf_n_plus_one_query_guard``."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_n_plus_one_query_guard"
    verbose_name = "DRF N+1 Query Guard"
