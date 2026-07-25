"""A complete notification preferences system for Django REST Framework.

The public API is intentionally small. Most projects only need:

* :func:`drf_notification.events.register` to declare each kind of
  notification the project sends.
* :func:`drf_notification.notify.notify` (or its async twin,
  :func:`drf_notification.async_notify.anotify`) to actually send one.
* ``path("notifications/", include("drf_notification.urls"))`` for the
  preference-center API.

Note:
    This module intentionally does **not** re-export :func:`notify`,
    :func:`anotify`, or any model class. Django imports every app's
    top-level ``__init__.py`` *before* any app's models are ready
    (during ``AppConfig`` discovery); importing a model-touching module
    from here would raise ``AppRegistryNotReady``. Import those directly
    from their submodule instead, e.g. ``from drf_notification.notify
    import notify`` or ``from drf_notification.models import
    Notification`` - see ``docs/quickstart.md`` for a complete
    end-to-end example.
"""

from __future__ import annotations

from drf_notification.backends.base import NotificationBackend
from drf_notification.events import (
    EventRegistry,
    EventType,
    default_registry,
    get_event_type,
    register,
)
from drf_notification.exceptions import (
    BackendDeliveryError,
    InvalidUnsubscribeTokenError,
    MissingTemplateError,
    NotificationError,
    UnknownEventTypeError,
)
from drf_notification.ratelimit import InvalidRateLimitError, is_rate_limited
from drf_notification.settings import app_settings, get_setting
from drf_notification.unsubscribe import generate_unsubscribe_token, resolve_unsubscribe_token
from drf_notification.url_safety import UnsafeWebhookUrlError, validate_public_url

__version__ = "1.0.0"

__all__ = [
    "BackendDeliveryError",
    "EventRegistry",
    "EventType",
    "InvalidRateLimitError",
    "InvalidUnsubscribeTokenError",
    "MissingTemplateError",
    "NotificationBackend",
    "NotificationError",
    "UnknownEventTypeError",
    "UnsafeWebhookUrlError",
    "__version__",
    "app_settings",
    "default_registry",
    "generate_unsubscribe_token",
    "get_event_type",
    "get_setting",
    "is_rate_limited",
    "register",
    "resolve_unsubscribe_token",
    "validate_public_url",
]
