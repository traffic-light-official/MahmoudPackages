"""Django settings integration for :mod:`drf_jwt_auth_kit`.

All configuration lives under a single Django setting, ``JWT_AUTH_KIT``, a
dictionary of overrides merged on top of :data:`DEFAULTS`. Settings are
validated and cached lazily on first access, and the cache is invalidated
automatically when Django's ``setting_changed`` signal fires (which makes
``@override_settings(JWT_AUTH_KIT={...})`` work correctly in tests).
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Final

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.signals import setting_changed
from django.utils.functional import cached_property

USER_SETTINGS_NAME: Final[str] = "JWT_AUTH_KIT"

#: Default values for every recognized setting. See ``docs/settings.md``
#: for the full description of each key.
DEFAULTS: Final[dict[str, Any]] = {
    #: How long an access token is valid for. Kept short since access
    #: tokens are verified statelessly (no database check on every
    #: request by default) - see ``CHECK_DEVICE_REVOCATION_ON_AUTH``.
    "ACCESS_TOKEN_LIFETIME": dt.timedelta(minutes=5),
    #: How long a normal (non-"remember me") refresh token is valid for.
    "REFRESH_TOKEN_LIFETIME": dt.timedelta(days=7),
    #: How long a "remember me" refresh token is valid for.
    "REMEMBER_ME_REFRESH_TOKEN_LIFETIME": dt.timedelta(days=30),
    #: JWT signing algorithm, passed straight to PyJWT.
    "ALGORITHM": "HS256",
    #: Key used to sign/verify tokens. When ``None``, falls back to
    #: Django's own ``SECRET_KEY``. Set explicitly (and rotate
    #: independently of ``SECRET_KEY``) for defense in depth, or set a
    #: public/private key pair here and in ``VERIFYING_KEY`` if
    #: ``ALGORITHM`` is asymmetric (e.g. ``RS256``).
    "SIGNING_KEY": None,
    #: Key used only to *verify* tokens, for asymmetric algorithms. When
    #: ``None``, ``SIGNING_KEY`` (or ``SECRET_KEY``) is used for both.
    "VERIFYING_KEY": None,
    #: JWT ``iss`` claim. When ``None``, the claim is omitted.
    "ISSUER": None,
    #: JWT ``aud`` claim (and the value verified against it). When
    #: ``None``, the claim is omitted and audience is not checked.
    "AUDIENCE": None,
    #: Name of the httpOnly cookie carrying the refresh token.
    "REFRESH_COOKIE_NAME": "refresh_token",
    #: ``Domain`` attribute of the refresh cookie. ``None`` omits it,
    #: scoping the cookie to the exact host that set it.
    "REFRESH_COOKIE_DOMAIN": None,
    #: ``Path`` attribute of the refresh cookie and the CSRF cookie.
    "REFRESH_COOKIE_PATH": "/",
    #: ``Secure`` attribute of the refresh cookie. Only disable this for
    #: local development over plain HTTP - never in production.
    "REFRESH_COOKIE_SECURE": True,
    #: ``SameSite`` attribute of the refresh cookie: ``"Lax"``,
    #: ``"Strict"``, or ``"None"`` (``"None"`` requires ``Secure=True``
    #: and is needed for cross-site SPA deployments).
    "REFRESH_COOKIE_SAMESITE": "Lax",
    #: Name of the (non-httpOnly, JavaScript-readable) double-submit CSRF
    #: cookie paired with the refresh cookie.
    "CSRF_COOKIE_NAME": "refresh_csrftoken",
    #: Name of the request header a client must echo the CSRF cookie's
    #: value back in for cookie-authenticated refresh/logout requests.
    "CSRF_HEADER_NAME": "X-Refresh-CSRFToken",
    #: When ``True`` (default), rotating a refresh token also marks the
    #: old one revoked in the database (the basis for reuse detection).
    #: Disabling this disables reuse detection entirely - not
    #: recommended.
    "BLACKLIST_AFTER_ROTATION": True,
    #: When ``True``, :class:`~drf_jwt_auth_kit.authentication.JWTAuthentication`
    #: performs one extra database query per request to confirm the
    #: access token's device has not been revoked, making logout-all
    #: take effect immediately instead of only once the access token
    #: naturally expires. Trades the "fully stateless" property of JWTs
    #: for tighter revocation - most projects do not need this given a
    #: short ``ACCESS_TOKEN_LIFETIME``.
    "CHECK_DEVICE_REVOCATION_ON_AUTH": False,
    #: Dotted path to the :class:`~drf_jwt_auth_kit.mfa.MFAProvider`
    #: subclass used during login. Defaults to a provider that never
    #: requires MFA.
    "MFA_PROVIDER": "drf_jwt_auth_kit.mfa.NullMFAProvider",
    #: Issuer name embedded in TOTP provisioning URIs (shown in
    #: authenticator apps next to the account name).
    "TOTP_ISSUER_NAME": "drf-jwt-auth-kit",
    #: Number of 30-second time steps of clock drift to tolerate on
    #: either side when verifying a TOTP code.
    "TOTP_VALID_WINDOW": 1,
    #: When ``True`` (default), every login attempt (success or failure)
    #: is recorded in :class:`~drf_jwt_auth_kit.models.LoginHistory`.
    "LOGIN_HISTORY_ENABLED": True,
}

_TYPE_CHECKS: Final[dict[str, type | tuple[type, ...]]] = {
    "ACCESS_TOKEN_LIFETIME": dt.timedelta,
    "REFRESH_TOKEN_LIFETIME": dt.timedelta,
    "REMEMBER_ME_REFRESH_TOKEN_LIFETIME": dt.timedelta,
    "ALGORITHM": str,
    "SIGNING_KEY": (str, type(None)),
    "VERIFYING_KEY": (str, type(None)),
    "ISSUER": (str, type(None)),
    "AUDIENCE": (str, type(None)),
    "REFRESH_COOKIE_NAME": str,
    "REFRESH_COOKIE_DOMAIN": (str, type(None)),
    "REFRESH_COOKIE_PATH": str,
    "REFRESH_COOKIE_SECURE": bool,
    "REFRESH_COOKIE_SAMESITE": str,
    "CSRF_COOKIE_NAME": str,
    "CSRF_HEADER_NAME": str,
    "BLACKLIST_AFTER_ROTATION": bool,
    "CHECK_DEVICE_REVOCATION_ON_AUTH": bool,
    "MFA_PROVIDER": str,
    "TOTP_ISSUER_NAME": str,
    "TOTP_VALID_WINDOW": int,
    "LOGIN_HISTORY_ENABLED": bool,
}

_VALID_SAMESITE: Final[frozenset[str]] = frozenset({"Lax", "Strict", "None"})


class _JWTAuthKitSettings:
    """Lazily-evaluated, validated, cache-invalidating settings object."""

    def __init__(self) -> None:
        setting_changed.connect(self._on_setting_changed)

    @cached_property
    def _user_settings(self) -> dict[str, Any]:
        raw = getattr(settings, USER_SETTINGS_NAME, {})
        if not isinstance(raw, dict):
            raise ImproperlyConfigured(
                f"The '{USER_SETTINGS_NAME}' Django setting must be a dict, "
                f"got {type(raw).__name__}."
            )
        unknown_keys = set(raw) - set(DEFAULTS)
        if unknown_keys:
            raise ImproperlyConfigured(
                f"Unknown key(s) in '{USER_SETTINGS_NAME}': {sorted(unknown_keys)}. "
                f"Valid keys are: {sorted(DEFAULTS)}."
            )
        merged = {**DEFAULTS, **raw}
        for key, expected_type in _TYPE_CHECKS.items():
            if not isinstance(merged[key], expected_type):
                raise ImproperlyConfigured(
                    f"'{USER_SETTINGS_NAME}[\"{key}\"]' must be of type "
                    f"{expected_type}, got {type(merged[key]).__name__}."
                )
        if merged["REFRESH_COOKIE_SAMESITE"] not in _VALID_SAMESITE:
            raise ImproperlyConfigured(
                f"'{USER_SETTINGS_NAME}[\"REFRESH_COOKIE_SAMESITE\"]' must be one of "
                f"{sorted(_VALID_SAMESITE)}, got {merged['REFRESH_COOKIE_SAMESITE']!r}."
            )
        if merged["REFRESH_COOKIE_SAMESITE"] == "None" and not merged["REFRESH_COOKIE_SECURE"]:
            raise ImproperlyConfigured(
                f'\'{USER_SETTINGS_NAME}["REFRESH_COOKIE_SAMESITE"]\' of "None" requires '
                f"'{USER_SETTINGS_NAME}[\"REFRESH_COOKIE_SECURE\"]' to be True."
            )
        if merged["TOTP_VALID_WINDOW"] < 0:
            raise ImproperlyConfigured(
                f"'{USER_SETTINGS_NAME}[\"TOTP_VALID_WINDOW\"]' must be >= 0."
            )
        return merged

    def __getitem__(self, key: str) -> Any:
        if key not in DEFAULTS:
            raise KeyError(f"Invalid setting: {key!r}. Valid keys are: {sorted(DEFAULTS)}.")
        return self._user_settings[key]

    def _on_setting_changed(self, *, sender: Any, setting: str, **kwargs: Any) -> None:
        if setting == USER_SETTINGS_NAME:
            self.__dict__.pop("_user_settings", None)


app_settings = _JWTAuthKitSettings()


def get_setting(key: str) -> Any:
    """Return the effective value of a single package setting.

    Args:
        key: One of the keys documented in :data:`DEFAULTS`.

    Returns:
        The user-configured value if present in the ``JWT_AUTH_KIT``
        Django setting, otherwise the default.

    Raises:
        KeyError: If ``key`` is not a recognized setting name.
        django.core.exceptions.ImproperlyConfigured: If the
            ``JWT_AUTH_KIT`` setting is malformed.
    """
    return app_settings[key]


def get_signing_key() -> str:
    """Return the effective signing key: ``SIGNING_KEY`` or Django's ``SECRET_KEY``."""
    signing_key = get_setting("SIGNING_KEY")
    result: str = signing_key if signing_key is not None else settings.SECRET_KEY
    return result


def get_verifying_key() -> str:
    """Return the effective verifying key: ``VERIFYING_KEY``, else the signing key."""
    verifying_key = get_setting("VERIFYING_KEY")
    return verifying_key if verifying_key is not None else get_signing_key()
