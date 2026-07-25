"""Management command: ``python manage.py scaffold_api``.

A convenience wrapper for projects that already run Django, so
scaffolding can be triggered as part of an existing ``manage.py``-based
workflow instead of installing/invoking the standalone CLI separately.
"""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from drf_api_reverse.checker import check_drift
from drf_api_reverse.exceptions import ApiReverseError
from drf_api_reverse.scaffolder import scaffold
from drf_api_reverse.schema_loader import load_schema_file


class Command(BaseCommand):
    """Scaffold or check DRF code against an OpenAPI contract."""

    help = "Generate/regenerate DRF serializers, viewsets, and urls from an OpenAPI schema."

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Register this command's options."""
        parser.add_argument("--schema", required=True, help="Path to the OpenAPI schema file.")
        parser.add_argument(
            "--output", required=True, help="Directory to write the generated files into."
        )
        parser.add_argument(
            "--check",
            action="store_true",
            help="Report drift instead of writing files; exit non-zero if any is found.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Scaffold or check, depending on ``--check``."""
        try:
            schema = load_schema_file(options["schema"])
        except (ApiReverseError, OSError) as exc:
            raise CommandError(str(exc)) from exc

        output_dir = Path(options["output"])

        if options["check"]:
            reports = check_drift(schema, output_dir)
            drifted = [report for report in reports if report.has_drift]
            for report in reports:
                status = "DRIFTED" if report.has_drift else "in sync"
                self.stdout.write(f"{report.filename}: {status}")
            if drifted:
                names = ", ".join(report.filename for report in drifted)
                raise CommandError(f"Generated code has drifted from the schema in: {names}.")
            return

        for result in scaffold(schema, output_dir):
            verb = "Created" if result.created else "Updated"
            self.stdout.write(f"{verb} {output_dir / result.filename}")
