"""Django app configuration.

Adding ``"drf_llm_gateway"`` to ``INSTALLED_APPS`` is only required if you
want to use the ``generate_llm_tools`` management command — Django only
discovers management commands from apps listed in ``INSTALLED_APPS``.
Every other feature (``expose_as_tool``, ``execute_tool``,
``to_openai_tools``, ``to_mcp_tools``, ...) works without it.
"""

from __future__ import annotations

from django.apps import AppConfig


class DrfLlmGatewayConfig(AppConfig):
    """App configuration for :mod:`drf_llm_gateway`."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_llm_gateway"
    verbose_name = "DRF LLM Gateway"
