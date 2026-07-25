# API Reference

This page documents every public class, function, and exception. It is
generated in part from the source docstrings via
[mkdocstrings](https://mkdocstrings.github.io/) - the same text you'll see
in your editor's tooltips.

## Sending notifications

### notify

::: drf_notification.notify.notify

### redeliver

::: drf_notification.notify.redeliver

### anotify

::: drf_notification.async_notify.anotify

## Event registry

### EventType

::: drf_notification.events.EventType

### EventRegistry

::: drf_notification.events.EventRegistry

### register

::: drf_notification.events.register

### get_event_type

::: drf_notification.events.get_event_type

## Models

### NotificationSettings

::: drf_notification.models.NotificationSettings

### NotificationPreference

::: drf_notification.models.NotificationPreference

### WebhookTarget

::: drf_notification.models.WebhookTarget

### NotificationTemplate

::: drf_notification.models.NotificationTemplate

### Notification

::: drf_notification.models.Notification

## Rendering

### render_notification

::: drf_notification.rendering.render_notification

## Quiet hours

### is_within_quiet_hours

::: drf_notification.quiet_hours.is_within_quiet_hours

## Rate limiting

### is_rate_limited

::: drf_notification.ratelimit.is_rate_limited

### parse_rate

::: drf_notification.ratelimit.parse_rate

## Unsubscribe tokens

### generate_unsubscribe_token

::: drf_notification.unsubscribe.generate_unsubscribe_token

### resolve_unsubscribe_token

::: drf_notification.unsubscribe.resolve_unsubscribe_token

## Webhook URL safety

### validate_public_url

::: drf_notification.url_safety.validate_public_url

## Backends

### NotificationBackend

::: drf_notification.backends.base.NotificationBackend

### EmailBackend

::: drf_notification.backends.email.EmailBackend

### ConsoleBackend

::: drf_notification.backends.console.ConsoleBackend

### InAppBackend

::: drf_notification.backends.inapp.InAppBackend

### WebhookBackend

::: drf_notification.backends.webhook.WebhookBackend

### get_backend

::: drf_notification.backends.registry.get_backend

## Digests

### send_digest_for_user

::: drf_notification.digest.send_digest_for_user

### send_due_digests

::: drf_notification.digest.send_due_digests

### collect_pending_digest_notifications

::: drf_notification.digest.collect_pending_digest_notifications

## DRF views

### NotificationViewSet

::: drf_notification.views.NotificationViewSet

### NotificationPreferenceViewSet

::: drf_notification.views.NotificationPreferenceViewSet

### WebhookTargetViewSet

::: drf_notification.views.WebhookTargetViewSet

### NotificationSettingsView

::: drf_notification.views.NotificationSettingsView

### UnsubscribeView

::: drf_notification.views.UnsubscribeView

### PreferenceCenterView

::: drf_notification.views.PreferenceCenterView

## Exceptions

### NotificationError

::: drf_notification.exceptions.NotificationError

### UnknownEventTypeError

::: drf_notification.exceptions.UnknownEventTypeError

### BackendDeliveryError

::: drf_notification.exceptions.BackendDeliveryError

### InvalidUnsubscribeTokenError

::: drf_notification.exceptions.InvalidUnsubscribeTokenError

### MissingTemplateError

::: drf_notification.exceptions.MissingTemplateError

## Settings

### get_setting

::: drf_notification.settings.get_setting
