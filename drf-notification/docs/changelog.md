# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-25

### Added

- Initial release.
- `notify()` / `anotify()` core delivery pipeline across five channels:
  email, SMS, push, in-app, and signed webhooks.
- `EventType` / `register()` code-level event type registry.
- `NotificationPreference` (per-user, per-event, per-channel opt-in/out),
  `NotificationSettings` (digest frequency, quiet hours, global
  unsubscribe), `WebhookTarget`, `NotificationTemplate`, and
  `Notification` models.
- Database-backed, admin-editable templates with a plain-text fallback.
- Quiet-hours evaluation with correct past-midnight wraparound.
- Digest batching (`send_digest_for_user`, `send_due_digests`) and the
  `send_digests` management command.
- Cache-backed per-channel rate limiting.
- Retry with exponential backoff, synchronously via
  `retry_failed_notifications` or asynchronously via the optional Celery
  task `drf_notification.tasks.deliver_notification_task`.
- Signed, stateless unsubscribe tokens (single-event or everything) and
  a persistent preference-center token.
- A best-effort SSRF guard (`drf_notification.url_safety`) on
  user-submitted webhook URLs.
- DRF ViewSets (`NotificationViewSet`, `NotificationPreferenceViewSet`,
  `WebhookTargetViewSet`), `NotificationSettingsView`, `UnsubscribeView`,
  `PreferenceCenterView`, and a ready-to-`include()` `drf_notification.urls`.
- Django admin registration for every model.
- Full test suite across Python 3.10-3.13 and Django 4.2-5.2.

[Unreleased]: https://github.com/MahmoudGShake/MahmoudPackages/compare/drf-notification-v1.0.0...HEAD
[1.0.0]: https://github.com/MahmoudGShake/MahmoudPackages/releases/tag/drf-notification-v1.0.0
