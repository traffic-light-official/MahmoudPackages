# Troubleshooting

## Every request gets a 400 "No tenant could be resolved"

`TenantMiddleware` rejects requests when no tenant resolves and
`MULTITENANT["STRICT"]` is `True` (the default). Check:

- The resolver you've configured matches how your client actually sends
  tenant information (header name, subdomain format, user attribute).
- `header_resolver`'s default header is `X-Tenant-ID` — confirm your
  client sends exactly that name (case-insensitive, but the value must
  be a valid pk).
- `TENANT_MODEL` is set correctly (`"app_label.ModelName"`) if using
  `header_resolver`/`subdomain_resolver`.
- The tenant row you're testing against actually exists.

## `ImproperlyConfigured: MULTITENANT['TENANT_MODEL'] must be set`

You're using `header_resolver` or `subdomain_resolver` without setting
`TENANT_MODEL`. Set it, or switch to `user_attr_resolver` (which doesn't
need to query the tenant model directly) or a custom resolver.

## A related field never accepts a valid pk

See [FAQ](faq.md#my-primarykeyrelatedfield-never-validates-any-pk-why) —
this is almost always an explicitly-declared
`PrimaryKeyRelatedField(queryset=Model.objects.all())` frozen empty at
import time. Let `ModelSerializer` auto-build the field instead.

## `NoTenantSetError` from `TenantScopedModel.save()`

You're saving an instance with no tenant assigned and no tenant bound in
the current context. Either:

- Assign the tenant field explicitly before saving, or
- Ensure `TenantMiddleware` ran (for a real request) or wrap the code in
  `tenant_context(...)` (for a script, task, or shell session).

## `TenantMismatchError` when saving

The instance already has a tenant assigned that differs from the
current context's tenant. This is deliberate — it means either your
current context is wrong for this operation, or you're accidentally
reusing an instance loaded under a different tenant. Double-check which
tenant context the save is actually happening under.

## `Author.objects.all()` returns nothing even inside a request

Confirm `TenantMiddleware` is actually installed in `MIDDLEWARE` (order
relative to other middleware rarely matters, but it must run before your
view). If it's installed and you still get nothing, check that the
resolver is actually finding a tenant for that specific request — add a
temporary log statement in your resolver, or test it directly with
`RequestFactory` as shown in [Testing](testing.md#testing-your-own-resolver).

## Tests pass individually but fail when run together

Check you aren't leaking a tenant context between tests — if you call
`set_current_tenant()` directly instead of the `tenant_context()`/
`as_tenant()` context manager, you're responsible for calling
`reset_current_tenant()` yourself. Prefer the context manager form; it
always resets, even on an exception.

## The Django admin shows no rows for a non-superuser

Confirm a tenant actually resolves for the admin request — the admin
goes through the same middleware stack, so if `STRICT` is `True` and no
tenant resolves, the request is rejected before reaching the admin at
all; if `STRICT` is `False`, `TenantAdminMixin` shows an empty
changelist for a request with no tenant, on purpose (never falls back to
showing every tenant's rows to a non-superuser).

## Still stuck?

Open a [GitHub Discussion](https://github.com/mahmoudgshaker/drf-multitenant/discussions)
with your `MULTITENANT` settings (redact anything sensitive) and the
exact resolver/middleware configuration you're using.
