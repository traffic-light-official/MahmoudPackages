# Troubleshooting

## My views still return DRF's default error shape

Check that `REST_FRAMEWORK["EXCEPTION_HANDLER"]` points at
`"drf_error_response_standardizer.handler.problem_details_exception_handler"`
(as a string, or the imported callable) in your Django settings, and
that the settings module actually used by your running process is the
one you edited. A `ViewSet` or `APIView` that overrides
`get_exception_handler()` directly bypasses the `REST_FRAMEWORK` setting
entirely - search your codebase for that override if the global setting
does not seem to take effect for a specific view.

## `ImproperlyConfigured: The 'ERROR_RESPONSE_STANDARDIZER' Django setting must be a dict`

You have set `ERROR_RESPONSE_STANDARDIZER` to something other than a
dict (a list, a string, `None`, etc.). It must be a `dict`, even if
empty: `ERROR_RESPONSE_STANDARDIZER = {}`.

## `ImproperlyConfigured: Unknown key(s) in 'ERROR_RESPONSE_STANDARDIZER'`

A typo in one of your setting keys. The error message lists every valid
key; cross-reference with [Settings](settings.md).

## `ImproperlyConfigured: 'ERROR_RESPONSE_STANDARDIZER["TYPE_BASE_URI"]' must end with '/'`

`TYPE_BASE_URI` is combined with an `ErrorType.slug` by simple string
concatenation (`f"{base_uri}{slug}"`), so it must end with a trailing
slash - `"https://api.example.com/problems"` (missing slash) is
rejected; `"https://api.example.com/problems/"` is accepted.

## My custom exception isn't getting the problem type I registered

Registration order matters relative to when the exception handler runs,
not relative to when the view module is imported - but Python module
import order can still matter if your `register()` call lives in a
module that is never actually imported before the first request. Put
registrations in an `AppConfig.ready()` method (see
[Configuration](configuration.md#custom-exception-mapping)) rather than
at the bottom of a views/serializers module, to guarantee they run
exactly once at Django startup.

Also check for a more specific registration shadowing yours: MRO
resolution means a mapping registered for a subclass always wins over
one registered for a base class, in either order of registration.

## Nested validation errors are missing from the `errors` array

Confirm `EXPAND_VALIDATION_ERRORS` has not been set to `False` (see
[Settings](settings.md#expand_validation_errors)). If it is enabled and
errors are still missing, check whether the raising code passed a
serializer instance's `.errors` (a fully validated error dict) versus
manually constructing a `ValidationError` with unexpected shape -
`normalize_validation_error` expects the same nested dict/list/`ErrorDetail`
shape DRF itself produces from `serializer.is_valid()`.

## `WWW-Authenticate` / `Retry-After` header missing

See [FAQ](faq.md#why-is-there-no-www-authenticate-header-on-my-401-response)
for `WWW-Authenticate`. For `Retry-After`, confirm the raised exception
is actually `rest_framework.exceptions.Throttled` (raised by DRF's
throttle classes automatically) - a custom exception mapped via the
registry does not automatically get a `Retry-After` header unless you
add one yourself via a custom builder that sets `exc.wait` before
raising, or by using `ProblemAPIException` extensions plus your own
middleware.

## Translations aren't applied to a custom `ErrorType.title`

Wrap the title with `django.utils.translation.gettext_lazy` (or call
`str(gettext_lazy(...))` at registration time only if you are certain
registration happens after Django's translation machinery is ready -
`AppConfig.ready()` is late enough). See
[Advanced Usage](advanced-usage.md#localization).

## Tests interfere with each other via a shared registry

If you called `register()`/`register_builder()` directly against
`default_registry` in a test, always `default_registry.unregister(...)`
in a `finally` block or fixture teardown - see
[Testing](testing.md#testing-a-custom-exception-mapping-in-isolation).
Prefer building a fresh `ProblemRegistry()` per test and passing it via
`registry=` when you don't specifically need to test global registration.
