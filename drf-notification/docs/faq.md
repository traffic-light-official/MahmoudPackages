# FAQ

## Does `notify()` support per-recipient language automatically?

Not automatically - `render_notification()` (which `notify()` calls
internally) defaults to `language="en"`. If your project stores a
per-user language preference, call
`drf_notification.rendering.render_notification()` yourself with the
right `language=`, or open an issue if you'd like `notify()` itself to
learn to resolve it from a configurable attribute path.

## Why does an in-app notification never get deferred by quiet hours?

Quiet hours and digesting exist to protect a user from an *interruption*
(an email ping, a push buzz) at a bad time. An in-app notification is
passive - it just waits in a list until the user opens the app - so
there's no interruption to defer. See
[Architecture](architecture.md#in-app-notifications-are-never-deferred).

## How do I make an event type always bypass quiet hours and digesting?

Pass `urgent=True` to `register()`:

```python
register("security.password_reset", "Password reset requested.", urgent=True)
```

## Can I use a custom user model?

Yes - every FK in this package targets `settings.AUTH_USER_MODEL`, and
`notify()`/`anotify()` accept any `Model` instance as `recipient`. The
only requirement `EmailBackend` has is that the instance expose an
`email` attribute (most custom user models already do, since Django's
`AbstractUser`/`AbstractBaseUser` conventions expect it).

## What happens if I call `notify()` for an event type I never registered?

`UnknownEventTypeError` is raised immediately, before any
`Notification` row is created. This is deliberate - a typo'd event key
should fail loudly during development/testing, not silently produce no
notification.

## Does this package send anything on its own (signals, etc.)?

No. `notify()` is only ever called by your own code, wherever you
choose to call it. This package does not attach any Django model
signals or automatically notify on any event; it has no opinion on
*when* you should notify, only *how*.

## How is this different from `django-notifications` or similar packages?

Most existing Django notification packages focus on the in-app
"activity feed" use case only. `drf-notification` treats in-app as one
of five channels with equal footing, and adds preference management,
digesting, quiet hours, rate limiting, retries, and a DRF-native
preference-center API as first-class, not as an afterthought.

## Can I disable the SSRF guard on webhook URLs?

Not directly - `WebhookTargetSerializer.validate_url()` always calls
`validate_public_url()`. If you need a different policy (e.g. an
allowlist of specific internal hosts for a trusted, internal-only
integration), subclass `WebhookTargetSerializer` and override
`validate_url()`, or create `WebhookTarget` rows directly via the ORM,
which bypasses serializer validation entirely (only do this for targets
you trust).

## Why is there no built-in push notification provider?

Real push delivery (FCM, APNs) requires provider-specific credentials,
device token management, and SDKs this package has no reason to bundle
or depend on. The default `ConsoleBackend` for `push` (and `sms`) is a
clearly-logged placeholder; wire in your provider via the `BACKENDS`
setting - see [Advanced Usage](advanced-usage.md#custom-backends).
