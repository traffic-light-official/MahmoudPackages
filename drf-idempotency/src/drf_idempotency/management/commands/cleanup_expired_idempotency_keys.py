"""``cleanup_expired_idempotency_keys`` management command.

The database backend has no native TTL, so expired records must be
removed periodically (via cron, Celery beat, or any other scheduler).
Reads that hit an expired record already treat it as absent (see
:meth:`drf_idempotency.backends.database.DatabaseBackend.get`), so running
this command is purely about reclaiming storage, not correctness.

.. code-block:: bash

    python manage.py cleanup_expired_idempotency_keys
"""

from __future__ import annotations

from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand

from drf_idempotency.core import get_backend


class Command(BaseCommand):
    """Delete expired idempotency records."""

    help = __doc__

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Register this command's CLI arguments.

        Args:
            parser: The argument parser to add options to.
        """
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Suppress the summary line on success.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Run the command.

        Args:
            *args: Unused positional arguments.
            **options: Parsed CLI options (``quiet``).
        """
        deleted = get_backend().cleanup_expired()
        if not options["quiet"]:
            self.stdout.write(
                self.style.SUCCESS(f"Removed {deleted} expired idempotency record(s).")
            )
