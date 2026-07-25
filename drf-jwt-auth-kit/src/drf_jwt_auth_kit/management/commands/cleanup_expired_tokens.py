"""Management command: ``python manage.py cleanup_expired_tokens``."""

from __future__ import annotations

import datetime as dt
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from drf_jwt_auth_kit.models import RefreshToken


class Command(BaseCommand):
    """Delete refresh token rows that expired more than a day ago.

    Expired and revoked tokens are already rejected by
    :func:`~drf_jwt_auth_kit.rotation.rotate_refresh_token`; this command
    only exists to keep the table from growing unbounded, and is safe to
    run on a schedule (e.g. daily via cron).
    """

    help = "Delete refresh token rows that expired more than a day ago."

    def handle(self, *args: Any, **options: Any) -> None:
        """Delete stale rows and report how many were removed."""
        cutoff = timezone.now() - dt.timedelta(days=1)
        deleted, _details = RefreshToken.objects.filter(expires_at__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} expired refresh token(s)."))
