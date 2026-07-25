"""Django app configuration for :mod:`drf_changelog_generator`."""

from __future__ import annotations

from django.apps import AppConfig


class ChangelogGeneratorConfig(AppConfig):
    """Registers this package as a Django app.

    This package has no models; add ``"drf_changelog_generator"`` to
    ``INSTALLED_APPS`` only to enable the ``generate_changelog``
    management command. The CLI (``drf-changelog-generator``) works
    without any Django project at all.
    """

    name = "drf_changelog_generator"
    verbose_name = "DRF Changelog Generator"
