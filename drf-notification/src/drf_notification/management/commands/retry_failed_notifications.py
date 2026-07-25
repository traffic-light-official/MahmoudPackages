"""Management command: ``python manage.py retry_failed_notifications``."""

from __future__ import annotations

from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand

from drf_notification.constants import STATUS_FAILED
from drf_notification.models import Notification
from drf_notification.notify import redeliver
from drf_notification.settings import get_setting


class Command(BaseCommand):
    """Reattempt delivery of failed notifications that have not exhausted their retries."""

    help = "Reattempt delivery of failed notifications that have not exhausted their retries."

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Register the optional ``--limit`` option."""
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum number of notifications to retry in this run.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Retry every eligible failed notification (or up to ``--limit`` of them)."""
        max_retries = get_setting("MAX_RETRIES")
        queryset = Notification.objects.filter(
            status=STATUS_FAILED, attempts__lt=max_retries
        ).order_by("created_at")

        limit: int | None = options["limit"]
        if limit is not None:
            queryset = queryset[:limit]

        retried = 0
        for notification in queryset:
            redeliver(notification)
            retried += 1

        self.stdout.write(self.style.SUCCESS(f"Retried {retried} failed notification(s)."))
