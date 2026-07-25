# Deployment

## Checklist

- [ ] `drf_permission_debugger` in `INSTALLED_APPS`.
- [ ] `PERMISSION_DEBUGGER["ENABLED"]` is `False` (the default) in
      production, or its `True` override is a deliberate, environment-
      gated decision (`ENABLED: os.environ.get("ENVIRONMENT") !=
      "production"`), not an accidental leftover from local debugging -
      see [Security](security.md).
- [ ] `RESTRICT_TO_STAFF` is `True` (the default) in any environment
      with real user accounts.
- [ ] If you rely on `get_permission_trace()` directly (bypassing the
      `ENABLED`/`RESTRICT_TO_STAFF` gates via your own
      `finalize_response` override, e.g. for metrics), confirm that
      override doesn't itself leak the trace over HTTP unintentionally.

## No database migrations, no persisted state

This package defines no models - there is nothing to migrate, and no
state persists between requests or between processes. Every trace is
built fresh per-request and discarded once the response is sent.

## Safe to leave installed even with `ENABLED: False` everywhere

With the default settings, mixing `PermissionDebugMixin` into a
viewset costs a small, fixed amount of per-request bookkeeping (see
[Performance](performance.md)) but exposes nothing over HTTP - there is
no need to conditionally install this package per-environment; the
`ENABLED` setting is the single, sufficient gate.

## Enabling temporarily for one investigation

Since the setting is validated and cache-invalidated via Django's
`setting_changed` signal, toggling it doesn't require a process
restart in a development/staging environment using
`@override_settings` or a hot-reloadable settings source - in a real
deployed environment, though, changing a Django setting still means a
redeploy or an environment-variable change plus a process restart, the
same as any other setting.
