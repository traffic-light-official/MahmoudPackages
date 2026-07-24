"""Resolving the identity a rate limit applies to.

A "key function" takes a request (and, optionally, the view handling it)
and returns a string identifying *who* (or *what*) is being rate limited —
the IP address, the authenticated user, an API key, a tenant, or any
combination. This string becomes part of the Redis key, so requests from
different identities never share a counter/bucket.

Every key function shares the signature ``(request, view=None) -> str``,
even ones that don't need ``view``, so they can be called uniformly and
combined via :func:`combine` without special-casing.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from drf_ratelimit_plus.exceptions import InvalidKeyError
from drf_ratelimit_plus.settings import get_setting

KeyFunc = Callable[..., str]


def by_ip(request: Any, view: Any = None) -> str:
    """Key by the client's IP address.

    Args:
        request: The incoming request.
        view: Unused; accepted for calling-convention consistency.

    Returns:
        ``X-Forwarded-For``'s first entry if present (the original client
        in a proxied setup), otherwise ``REMOTE_ADDR``.
    """
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return str(forwarded).split(",")[0].strip()
    return str(request.META.get("REMOTE_ADDR", "unknown"))


def by_user(request: Any, view: Any = None) -> str:
    """Key by the authenticated user, falling back to IP for anonymous requests.

    Args:
        request: The incoming request.
        view: Unused; accepted for calling-convention consistency.

    Returns:
        ``f"user:{pk}"`` for an authenticated user, otherwise the same
        value :func:`by_ip` would produce.
    """
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return f"user:{user.pk}"
    return by_ip(request)


def by_api_key(request: Any, view: Any = None) -> str:
    """Key by an API key header, falling back to IP if absent.

    Args:
        request: The incoming request.
        view: Unused; accepted for calling-convention consistency.

    Returns:
        ``f"apikey:{value}"`` using the header named by the
        ``API_KEY_HEADER`` setting, or the same value :func:`by_ip` would
        produce if the header is missing.
    """
    header = get_setting("API_KEY_HEADER")
    value = request.headers.get(header)
    if value:
        return f"apikey:{value}"
    return by_ip(request)


def by_tenant(request: Any, view: Any = None) -> str:
    """Key by a tenant identifier attached to the request, falling back to IP.

    Args:
        request: The incoming request.
        view: Unused; accepted for calling-convention consistency.

    Returns:
        ``f"tenant:{value}"`` using the attribute named by the
        ``TENANT_ATTR`` setting, or the same value :func:`by_ip` would
        produce if that attribute is absent or ``None``.
    """
    attr = get_setting("TENANT_ATTR")
    value = getattr(request, attr, None)
    if value is not None:
        return f"tenant:{value}"
    return by_ip(request)


def by_view(request: Any, view: Any = None) -> str:
    """Key by the view/endpoint handling the request.

    Args:
        request: The incoming request.
        view: The view instance handling it, if available.

    Returns:
        A dotted path identifying the view's class, or the request path
        if no view instance is available (e.g. a function-based view
        calling this directly).
    """
    if view is not None:
        cls = type(view)
        return f"view:{cls.__module__}.{cls.__qualname__}"
    return f"path:{request.path}"


_BUILTIN_KEY_FUNCS: dict[str, KeyFunc] = {
    "ip": by_ip,
    "user": by_user,
    "api_key": by_api_key,
    "tenant": by_tenant,
    "view": by_view,
}


def resolve_key_func(key: str | KeyFunc) -> KeyFunc:
    """Resolve a key specification to a callable.

    Args:
        key: Either a callable already matching the ``(request, view=None)
            -> str`` signature, or the name of a built-in key function:
            ``"ip"``, ``"user"``, ``"api_key"``, ``"tenant"``, or
            ``"view"``.

    Returns:
        The resolved key function.

    Raises:
        drf_ratelimit_plus.exceptions.InvalidKeyError: If ``key`` is a
            string that doesn't name a built-in key function.
    """
    if callable(key):
        return key
    func = _BUILTIN_KEY_FUNCS.get(key)
    if func is None:
        raise InvalidKeyError(
            f"Unknown key function {key!r}. Built-in options: {sorted(_BUILTIN_KEY_FUNCS)}, "
            f"or pass a callable."
        )
    return func


def combine(*key_funcs: str | KeyFunc) -> KeyFunc:
    """Combine multiple key functions into one, joined by ``|``.

    Useful for compound scoping, e.g. per-tenant-per-user:
    ``combine("tenant", "user")``.

    Args:
        *key_funcs: Key specifications (names or callables), applied in
            order and joined with ``|``.

    Returns:
        A single key function producing the joined result.

    Example:
        >>> from unittest.mock import Mock
        >>> request = Mock(user=Mock(is_authenticated=True, pk=42), META={}, headers={})
        >>> request.tenant_id = "acme"
        >>> combine("tenant", "user")(request)
        'tenant:acme|user:42'
    """
    resolved = [resolve_key_func(k) for k in key_funcs]

    def _combined(request: Any, view: Any = None) -> str:
        return "|".join(func(request, view) for func in resolved)

    return _combined
