"""Delivers by POSTing a signed JSON payload to a user's webhook targets."""

from __future__ import annotations

import hashlib
import hmac
import json
import urllib.error
import urllib.request

from drf_notification.backends.base import NotificationBackend
from drf_notification.constants import WEBHOOK_EVENT_HEADER, WEBHOOK_SIGNATURE_HEADER
from drf_notification.exceptions import BackendDeliveryError
from drf_notification.models import Notification, WebhookTarget
from drf_notification.settings import get_setting


class WebhookBackend(NotificationBackend):
    """POSTs a signed JSON payload to every active :class:`~drf_notification.models.WebhookTarget`.

    The request body is signed with HMAC-SHA256 using each target's own
    ``secret`` and sent as ``X-Notification-Signature: sha256=<hex>``, the
    same convention GitHub and Stripe use, so recipients can verify
    authenticity before trusting the payload.
    """

    def send(self, notification: Notification) -> None:
        targets = list(
            WebhookTarget.objects.filter(user_id=notification.recipient_id, is_active=True)
        )
        if not targets:
            raise BackendDeliveryError(
                f"User {notification.recipient_id} has no active webhook targets."
            )

        payload = json.dumps(
            {
                "event": notification.event_key,
                "subject": notification.subject,
                "body": notification.body,
                "context": notification.context,
            }
        ).encode("utf-8")

        errors: list[str] = []
        delivered = 0
        for target in targets:
            try:
                self._post(target, payload, notification.event_key)
                delivered += 1
            except (urllib.error.URLError, OSError, TimeoutError) as exc:
                errors.append(f"{target.url}: {exc}")

        if delivered == 0:
            raise BackendDeliveryError("; ".join(errors) or "No webhook targets could be reached.")

    def _post(self, target: WebhookTarget, payload: bytes, event_key: str) -> None:
        signature = hmac.new(target.secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        request = urllib.request.Request(
            target.url,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                WEBHOOK_SIGNATURE_HEADER: f"sha256={signature}",
                WEBHOOK_EVENT_HEADER: event_key,
            },
        )
        timeout = get_setting("WEBHOOK_TIMEOUT")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status >= 400:
                raise BackendDeliveryError(f"Webhook {target.url} responded {response.status}.")
