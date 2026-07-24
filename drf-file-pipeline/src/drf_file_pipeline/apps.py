"""Django app configuration for :mod:`drf_file_pipeline`."""

from __future__ import annotations

from django.apps import AppConfig


class DrfFilePipelineConfig(AppConfig):
    name = "drf_file_pipeline"
    verbose_name = "File Pipeline"
    default_auto_field = "django.db.models.BigAutoField"
