# Deployment

## Checklist

- [ ] `drf_notification` in `INSTALLED_APPS`, migrations applied.
- [ ] Real backends configured for every channel you actually use -
      the shipped defaults for `sms`/`push` only log to the console
      (`ConsoleBackend`); replace them via the `BACKENDS` setting before
      relying on either channel in production.
- [ ] `DEFAULT_FROM_EMAIL` (or the `FROM_EMAIL` setting) set to a real,
      deliverable address; Django's own `EMAIL_BACKEND` pointed at a real
      SMTP provider (not the console/locmem backend used in development).
- [ ] `RATE_LIMITS` reviewed for your expected notification volume - the
      defaults are conservative starting points, not tuned for your
      traffic.
- [ ] A scheduler (cron, Celery beat, etc.) configured to run
      `send_digests --frequency=daily` and `--frequency=weekly` on the
      matching cadence, if you use non-immediate digest frequencies.
- [ ] A scheduler configured to run `retry_failed_notifications`
      periodically, if `USE_CELERY = False` (Celery mode retries
      automatically via task backoff).
- [ ] If `USE_CELERY = True`: a Celery worker running, `drf_notification`
      discoverable by `app.autodiscover_tasks()`, and a real broker/result
      backend configured (not the in-memory ones used for testing).
- [ ] Webhook targets reviewed for SSRF exposure if end users can supply
      arbitrary URLs - see [Security](security.md#webhook-urls-and-ssrf).

## Digest and retry scheduling

Without Celery, use your platform's cron/scheduled-task mechanism:

```cron
0 8 * * * cd /app && python manage.py send_digests --frequency=daily
0 8 * * 1 cd /app && python manage.py send_digests --frequency=weekly
*/15 * * * * cd /app && python manage.py retry_failed_notifications
```

With Celery, add periodic tasks via Celery beat instead:

```python
CELERY_BEAT_SCHEDULE = {
    "send-daily-digests": {
        "task": "drf_notification.send_daily_digests",  # your own thin wrapper task
        "schedule": crontab(hour=8, minute=0),
    },
}
```

(This package does not ship a Celery beat schedule itself, since
scheduling policy - what time, what timezone - is a deployment decision,
not a library concern.)

## Multi-region / multi-language deployments

Templates are looked up per `(event_key, channel, language)`, with a
fallback to `"en"`. Store per-recipient language preference on your own
user model or profile, and pass `language=` explicitly to
`render_notification()` if you call it directly; `notify()` itself
always renders in `"en"` unless you extend it (see
[FAQ](faq.md#does-notify-support-per-recipient-language-automatically)).

## Zero-downtime rollout

Adding `drf_notification` to an existing project is purely additive: new
tables, new URLs (only if you `include()` them), no changes to existing
models or endpoints. The one thing to plan for is registering event
types before any code path that calls `notify()` for them runs -
`AppConfig.ready()` (see [Getting Started](getting-started.md)) already
guarantees this at Django startup, so a rolling deploy that restarts
every process picks up new event types atomically with the code that
registers them.
