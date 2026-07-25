"""Signed, stateless unsubscribe tokens for a single event type.

A signed token (via :mod:`django.core.signing`) lets an email/SMS/webhook
recipient unsubscribe from one specific event type without logging in,
without a database round trip to validate it, and with a built-in
expiry. For "unsubscribe from everything" links, use the persistent,
non-expiring :attr:`~drf_notification.models.NotificationSettings.unsubscribe_token`
instead - see :mod:`drf_notification.views`.
"""

from __future__ import annotations

from django.core import signing

from drf_notification.constants import UNSUBSCRIBE_ALL_EVENTS, UNSUBSCRIBE_SIGNING_SALT
from drf_notification.exceptions import InvalidUnsubscribeTokenError
from drf_notification.settings import get_setting


def _signer() -> signing.TimestampSigner:
    return signing.TimestampSigner(salt=UNSUBSCRIBE_SIGNING_SALT)


def generate_unsubscribe_token(user_id: int, event_key: str | None = None) -> str:
    """Generate a signed, self-contained unsubscribe token.

    Args:
        user_id: Primary key of the user the link should unsubscribe.
        event_key: The event type to unsubscribe from, or ``None`` to
            unsubscribe from every event type.

    Returns:
        An opaque, URL-safe signed token. Embed it in an unsubscribe
        link; resolve it later with :func:`resolve_unsubscribe_token`.
    """
    payload = f"{user_id}:{event_key or UNSUBSCRIBE_ALL_EVENTS}"
    return _signer().sign(payload)


def resolve_unsubscribe_token(token: str) -> tuple[int, str | None]:
    """Verify and decode a token produced by :func:`generate_unsubscribe_token`.

    Args:
        token: The token to verify.

    Returns:
        A ``(user_id, event_key)`` tuple. ``event_key`` is ``None`` if the
        token was generated for "unsubscribe from everything".

    Raises:
        InvalidUnsubscribeTokenError: If the token is malformed, has been
            tampered with, or is older than the ``UNSUBSCRIBE_TOKEN_MAX_AGE``
            setting.
    """
    max_age = get_setting("UNSUBSCRIBE_TOKEN_MAX_AGE")
    try:
        payload = _signer().unsign(token, max_age=max_age)
    except signing.BadSignature as exc:
        raise InvalidUnsubscribeTokenError("Unsubscribe link is invalid or has expired.") from exc

    user_id_str, _, event_key = payload.partition(":")
    try:
        user_id = int(user_id_str)
    except ValueError as exc:
        raise InvalidUnsubscribeTokenError("Unsubscribe link is malformed.") from exc
    return user_id, None if event_key == UNSUBSCRIBE_ALL_EVENTS else event_key
