"""Management command: ``python manage.py list_api_versions``.

A quick, scriptable inventory of every declared version and its
lifecycle status - useful in CI (to catch a version silently past its
sunset date with ``ALLOW_SUNSET`` still true) or for a human checking
what's currently live before writing release notes.
"""

from __future__ import annotations

from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand

from drf_api_versioning import registry


class Command(BaseCommand):
    """List every declared API version and its lifecycle status."""

    help = "List every declared API version, its deprecation/sunset dates, and its status."

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Register this command's options."""
        parser.add_argument(
            "--status",
            choices=["supported", "deprecated", "sunset"],
            default=None,
            help="Only list versions currently in this status.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Print one line per declared version, filtered by ``--status`` if given."""
        status_filter = options["status"]
        default_name = registry.default_version_name()

        for info in registry.all_versions():
            status = _status_of(info)
            if status_filter is not None and status != status_filter:
                continue

            marker = " (default)" if info.name == default_name else ""
            line = f"{info.name}{marker}: {status}"
            if info.deprecated_on is not None:
                line += f", deprecated {info.deprecated_on.isoformat()}"
            if info.sunset_on is not None:
                line += f", sunset {info.sunset_on.isoformat()}"
            if info.deprecation_link is not None:
                line += f" ({info.deprecation_link})"
            self.stdout.write(line)


def _status_of(info: registry.VersionInfo) -> str:
    if info.is_sunset():
        return "sunset"
    if info.is_deprecated():
        return "deprecated"
    return "supported"
