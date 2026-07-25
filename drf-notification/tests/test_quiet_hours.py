"""Tests for :mod:`drf_notification.quiet_hours`."""

from __future__ import annotations

import datetime as dt

import pytest

from drf_notification.models import NotificationSettings
from drf_notification.quiet_hours import is_within_quiet_hours


@pytest.fixture
def user_settings(db: None, user: object) -> NotificationSettings:
    return NotificationSettings.objects.create(user=user)


class TestIsWithinQuietHours:
    def test_false_when_not_configured(self, user_settings: NotificationSettings) -> None:
        now = dt.datetime(2026, 1, 1, 23, 0, tzinfo=dt.timezone.utc)

        assert is_within_quiet_hours(user_settings, now=now) is False

    def test_false_when_only_start_configured(self, user_settings: NotificationSettings) -> None:
        user_settings.quiet_hours_start = dt.time(22, 0)
        now = dt.datetime(2026, 1, 1, 23, 0, tzinfo=dt.timezone.utc)

        assert is_within_quiet_hours(user_settings, now=now) is False

    def test_same_day_window(self, user_settings: NotificationSettings) -> None:
        user_settings.timezone_name = "UTC"
        user_settings.quiet_hours_start = dt.time(9, 0)
        user_settings.quiet_hours_end = dt.time(17, 0)

        inside = dt.datetime(2026, 1, 1, 12, 0, tzinfo=dt.timezone.utc)
        before = dt.datetime(2026, 1, 1, 8, 0, tzinfo=dt.timezone.utc)
        after = dt.datetime(2026, 1, 1, 18, 0, tzinfo=dt.timezone.utc)

        assert is_within_quiet_hours(user_settings, now=inside) is True
        assert is_within_quiet_hours(user_settings, now=before) is False
        assert is_within_quiet_hours(user_settings, now=after) is False

    def test_wraparound_window_past_midnight(self, user_settings: NotificationSettings) -> None:
        user_settings.timezone_name = "UTC"
        user_settings.quiet_hours_start = dt.time(22, 0)
        user_settings.quiet_hours_end = dt.time(7, 0)

        late_night = dt.datetime(2026, 1, 1, 23, 30, tzinfo=dt.timezone.utc)
        early_morning = dt.datetime(2026, 1, 2, 5, 0, tzinfo=dt.timezone.utc)
        midday = dt.datetime(2026, 1, 1, 12, 0, tzinfo=dt.timezone.utc)

        assert is_within_quiet_hours(user_settings, now=late_night) is True
        assert is_within_quiet_hours(user_settings, now=early_morning) is True
        assert is_within_quiet_hours(user_settings, now=midday) is False

    def test_boundary_start_is_inclusive_end_is_exclusive(
        self, user_settings: NotificationSettings
    ) -> None:
        user_settings.timezone_name = "UTC"
        user_settings.quiet_hours_start = dt.time(22, 0)
        user_settings.quiet_hours_end = dt.time(7, 0)

        at_start = dt.datetime(2026, 1, 1, 22, 0, tzinfo=dt.timezone.utc)
        at_end = dt.datetime(2026, 1, 2, 7, 0, tzinfo=dt.timezone.utc)

        assert is_within_quiet_hours(user_settings, now=at_start) is True
        assert is_within_quiet_hours(user_settings, now=at_end) is False

    def test_respects_configured_timezone(self, user_settings: NotificationSettings) -> None:
        user_settings.timezone_name = "America/New_York"
        user_settings.quiet_hours_start = dt.time(22, 0)
        user_settings.quiet_hours_end = dt.time(7, 0)

        # 2026-01-02 02:00 UTC == 2026-01-01 21:00 America/New_York (UTC-5) -> not yet quiet.
        just_before = dt.datetime(2026, 1, 2, 2, 0, tzinfo=dt.timezone.utc)
        # 2026-01-02 03:30 UTC == 2026-01-01 22:30 America/New_York -> quiet.
        inside = dt.datetime(2026, 1, 2, 3, 30, tzinfo=dt.timezone.utc)

        assert is_within_quiet_hours(user_settings, now=just_before) is False
        assert is_within_quiet_hours(user_settings, now=inside) is True

    def test_defaults_to_project_timezone_when_unset(
        self, user_settings: NotificationSettings
    ) -> None:
        user_settings.timezone_name = ""
        user_settings.quiet_hours_start = dt.time(9, 0)
        user_settings.quiet_hours_end = dt.time(17, 0)
        now = dt.datetime(2026, 1, 1, 12, 0, tzinfo=dt.timezone.utc)

        assert is_within_quiet_hours(user_settings, now=now) is True
