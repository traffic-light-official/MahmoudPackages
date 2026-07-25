"""Management command: ``python manage.py send_digests --frequency=daily``."""

from __future__ import annotations

from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from drf_notification.constants import DIGEST_DAILY, DIGEST_WEEKLY
from drf_notification.digest import send_due_digests


class Command(BaseCommand):
    """Send a batched digest to every user whose digest frequency matches."""

    help = "Send a batched digest to every user whose digest_frequency matches --frequency."

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Register the required ``--frequency`` option."""
        parser.add_argument(
            "--frequency",
            required=True,
            choices=[DIGEST_DAILY, DIGEST_WEEKLY],
            help="Which digest frequency to send for.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Send digests and report how many users received one."""
        frequency: str = options["frequency"]
        try:
            sent_for = send_due_digests(frequency)
        except Exception as exc:
            raise CommandError(f"Failed to send digests: {exc}") from exc
        self.stdout.write(self.style.SUCCESS(f"Sent {frequency} digests to {sent_for} user(s)."))
