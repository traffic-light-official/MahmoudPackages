"""Quiet-hours evaluation.

A user's quiet hours are a daily local time window during which
non-urgent notifications should not be delivered immediately - see
:func:`drf_notification.notify.notify`, which queues them for the next
digest instead.
"""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from drf_notification.models import NotificationSettings


def is_within_quiet_hours(
    user_settings: NotificationSettings, *, now: dt.datetime | None = None
) -> bool:
    """Return whether ``now`` falls within ``user_settings``'s quiet hours.

    Correctly handles a window that wraps past midnight (e.g.
    ``22:00``-``07:00``) and converts ``now`` into the user's configured
    timezone (or the project's ``TIME_ZONE`` if none is set) before
    comparing.

    Args:
        user_settings: The recipient's notification settings.
        now: The moment to evaluate. Defaults to the current time.

    Returns:
        ``False`` if quiet hours are not configured (either bound is
        ``None``); otherwise whether ``now`` falls inside the window.
    """
    start = user_settings.quiet_hours_start
    end = user_settings.quiet_hours_end
    if start is None or end is None:
        return False

    moment = now or timezone.now()
    tz_name = user_settings.timezone_name or settings.TIME_ZONE
    local_time = moment.astimezone(ZoneInfo(tz_name)).time()

    if start <= end:
        return start <= local_time < end
    # The window wraps past midnight.
    return local_time >= start or local_time < end
