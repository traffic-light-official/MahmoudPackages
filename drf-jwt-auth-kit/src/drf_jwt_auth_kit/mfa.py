"""MFA extension hooks, with a built-in RFC 6238 TOTP provider.

Plug in your own factor (SMS OTP, WebAuthn, backup codes, ...) by
subclassing :class:`MFAProvider` and pointing the ``MFA_PROVIDER``
setting at it. The default, :class:`NullMFAProvider`, never requires MFA.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from abc import ABC, abstractmethod
from urllib.parse import quote, urlencode

from django.db.models import Model
from django.utils.module_loading import import_string

from drf_jwt_auth_kit.models import TOTPDevice
from drf_jwt_auth_kit.settings import get_setting

_TOTP_DIGITS = 6
_TOTP_STEP_SECONDS = 30


class MFAProvider(ABC):
    """Base class for a multi-factor authentication check performed during login."""

    @abstractmethod
    def is_required(self, user: Model) -> bool:
        """Return whether ``user`` must supply an MFA code to log in.

        Args:
            user: The user who just presented valid credentials.
        """
        raise NotImplementedError

    @abstractmethod
    def verify(self, user: Model, code: str) -> bool:
        """Return whether ``code`` is a valid MFA code for ``user`` right now.

        Args:
            user: The user attempting to log in.
            code: The MFA code supplied with the login request.
        """
        raise NotImplementedError


class NullMFAProvider(MFAProvider):
    """The default provider: MFA is never required."""

    def is_required(self, user: Model) -> bool:
        return False

    def verify(self, user: Model, code: str) -> bool:
        return True


class TOTPProvider(MFAProvider):
    """RFC 6238 TOTP, backed by :class:`~drf_jwt_auth_kit.models.TOTPDevice`."""

    def is_required(self, user: Model) -> bool:
        # django-stubs resolves the user FK to this project's own
        # AUTH_USER_MODEL, which cannot generalize across the arbitrary
        # host-project user models a reusable app must accept.
        return TOTPDevice.objects.filter(user=user, confirmed=True).exists()  # type: ignore[misc]

    def verify(self, user: Model, code: str) -> bool:
        try:
            totp_device = TOTPDevice.objects.get(user=user, confirmed=True)  # type: ignore[misc]
        except TOTPDevice.DoesNotExist:
            return False
        return verify_totp_code(totp_device.secret, code)


def generate_totp_secret() -> str:
    """Generate a new random base32-encoded TOTP secret."""
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def totp_provisioning_uri(*, secret: str, account_name: str) -> str:
    """Build an ``otpauth://`` URI suitable for rendering as a QR code.

    Args:
        secret: The base32-encoded TOTP secret.
        account_name: A label identifying the account, e.g. the user's
            email address, shown in the authenticator app.

    Returns:
        An ``otpauth://totp/...`` URI.
    """
    issuer = get_setting("TOTP_ISSUER_NAME")
    label = quote(f"{issuer}:{account_name}")
    query = urlencode(
        {
            "secret": secret,
            "issuer": issuer,
            "algorithm": "SHA1",
            "digits": _TOTP_DIGITS,
            "period": _TOTP_STEP_SECONDS,
        }
    )
    return f"otpauth://totp/{label}?{query}"


def generate_totp_code(secret: str, *, at: float | None = None) -> str:
    """Generate the TOTP code for ``secret`` at a given time.

    Args:
        secret: The base32-encoded TOTP secret.
        at: Unix timestamp to generate the code for. Defaults to now.

    Returns:
        A zero-padded, 6-digit numeric code.
    """
    counter = int((at if at is not None else time.time()) // _TOTP_STEP_SECONDS)
    return _hotp(secret, counter)


def verify_totp_code(secret: str, code: str, *, at: float | None = None) -> bool:
    """Verify ``code`` against ``secret``, tolerating clock drift.

    Args:
        secret: The base32-encoded TOTP secret.
        code: The code to verify.
        at: Unix timestamp to verify against. Defaults to now.

    Returns:
        Whether ``code`` matches any time step within
        ``TOTP_VALID_WINDOW`` steps of ``at``.
    """
    if not code.isdigit() or len(code) != _TOTP_DIGITS:
        return False
    now = at if at is not None else time.time()
    window: int = get_setting("TOTP_VALID_WINDOW")
    counter = int(now // _TOTP_STEP_SECONDS)
    return any(
        hmac.compare_digest(_hotp(secret, counter + offset), code)
        for offset in range(-window, window + 1)
    )


def _hotp(secret: str, counter: int) -> str:
    padded_secret = secret.upper() + "=" * (-len(secret) % 8)
    key = base64.b32decode(padded_secret)
    message = struct.pack(">Q", counter)
    digest = hmac.new(key, message, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    truncated = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(truncated % (10**_TOTP_DIGITS)).zfill(_TOTP_DIGITS)


def get_mfa_provider() -> MFAProvider:
    """Instantiate the configured :class:`MFAProvider` (the ``MFA_PROVIDER`` setting)."""
    provider_class: type[MFAProvider] = import_string(get_setting("MFA_PROVIDER"))
    return provider_class()
