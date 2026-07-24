"""Management command: ``python manage.py generate_error_catalog``."""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from drf_error_response_standardizer.catalog import build_catalog, render_json, render_markdown


class Command(BaseCommand):
    """Generate the RFC 9457 error catalog for this project's registered problem types."""

    help = "Generate the RFC 9457 error catalog for this project's registered problem types."

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Register the ``--format`` and ``--output`` command-line options."""
        parser.add_argument(
            "--format",
            choices=["markdown", "json"],
            default="markdown",
            help="Output format (default: markdown).",
        )
        parser.add_argument(
            "--output",
            type=Path,
            default=None,
            help="Write the catalog to this file instead of stdout.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Build the catalog and write it to stdout or the requested file."""
        catalog = build_catalog()
        output_format = options["format"]
        rendered = render_markdown(catalog) if output_format == "markdown" else render_json(catalog)

        # ``call_command(..., output="some/path")`` bypasses argparse's
        # ``type=Path`` coercion and passes the raw string through, so we
        # normalize here rather than relying on the parser having run.
        raw_output = options["output"]
        output_path = Path(raw_output) if raw_output is not None else None
        if output_path is not None:
            output_path.write_text(rendered, encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Wrote {len(catalog)} entries to {output_path}"))
        else:
            self.stdout.write(rendered)
