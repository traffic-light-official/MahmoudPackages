# Testing

## Running this package's own test suite

```bash
pip install -e ".[test]"
pytest
```

With coverage:

```bash
pytest --cov --cov-report=term-missing
```

Across the full Python/Django support matrix via [tox](https://tox.wiki):

```bash
tox
```

## Testing that `notify()` sent what you expect

Use Django's email test backend (`django.core.mail.outbox`) for the
`email` channel:

```python
from django.core import mail


def test_order_shipped_email(user):
    notify(recipient=user, event_key="order.shipped", channels=["email"])

    assert len(mail.outbox) == 1
```

## Testing custom backends

Register a small recording backend via `override_settings` rather than
asserting on real network/SMS/push calls:

```python
from django.test import override_settings

from drf_notification.backends.base import NotificationBackend


class RecordingBackend(NotificationBackend):
    sent = []

    def send(self, notification):
        RecordingBackend.sent.append(notification)


def test_sms_is_attempted(user):
    with override_settings(NOTIFICATIONS={"BACKENDS": {"sms": "myapp.tests.RecordingBackend"}}):
        notify(recipient=user, event_key="order.shipped", channels=["sms"])

    assert len(RecordingBackend.sent) == 1
```

The backend class must be importable by its dotted path (i.e. defined
at module level, not nested inside a test function).

## Clearing rate-limit state between tests

The rate limiter is backed by Django's cache framework, which - unlike
the database - is **not** reset between tests automatically. If your
test suite exercises rate-limited channels, clear the cache in an
autouse fixture:

```python
import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
```

This package's own test suite does exactly this in `tests/conftest.py`
- a leaked rate-limit counter from an earlier test caused a real,
initially confusing failure during development; see
[Troubleshooting](troubleshooting.md#a-rate-limit-test-fails-intermittently-or-only-when-run-with-other-tests).

## Testing quiet hours and digests deterministically

Pass an explicit `now` to `is_within_quiet_hours()` rather than relying
on the real clock:

```python
import datetime as dt

from drf_notification.quiet_hours import is_within_quiet_hours

assert is_within_quiet_hours(settings_obj, now=dt.datetime(2026, 1, 1, 23, 0, tzinfo=dt.timezone.utc))
```

## Fixtures used by this package's own suite

`tests/conftest.py` provides `api_rf`, `api_client`, `user`, `other_user`,
and `authenticated_client` fixtures, plus the autouse cache-clearing
fixture described above - copy this pattern into your own project's
`conftest.py` if you do not already have equivalents.
