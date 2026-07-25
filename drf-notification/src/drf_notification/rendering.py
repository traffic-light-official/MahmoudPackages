"""Renders a notification's subject and body from a template.

Templates are looked up in the database
(:class:`~drf_notification.models.NotificationTemplate`) first, falling back
to a plain default derived from the event type's ``description`` when no
matching row exists - so a project can start sending a new event type
immediately and only add a polished template later.
"""

from __future__ import annotations

from django.template import Context, Template

from drf_notification.events import EventType, get_event_type
from drf_notification.exceptions import MissingTemplateError
from drf_notification.models import NotificationTemplate


def render_notification(
    *, event_key: str, channel: str, context: dict[str, object], language: str = "en"
) -> tuple[str, str]:
    """Render the subject and body for a notification.

    Args:
        event_key: The event type key.
        channel: The delivery channel, used to select a channel-specific
            template (an email and an SMS for the same event usually have
            very different content).
        context: Template context variables.
        language: BCP 47-ish language code matching
            :attr:`~drf_notification.models.NotificationTemplate.language`.
            Falls back to ``"en"`` if no template exists for the requested
            language.

    Returns:
        A ``(subject, body)`` tuple. ``subject`` is an empty string for
        channels that have no concept of a subject line (SMS, push,
        webhook) unless a template explicitly provides one.

    Raises:
        MissingTemplateError: If no database template exists and the
            event type itself is not registered either (so no fallback
            description is available).
    """
    template = _find_template(event_key, channel, language)
    if template is not None:
        return (
            _render_string(template.subject_template, context),
            _render_string(template.body_template, context),
        )

    event = get_event_type(event_key)
    if event is None:
        raise MissingTemplateError(event_key, channel)
    return _default_subject(event), _default_body(event, context)


def _find_template(event_key: str, channel: str, language: str) -> NotificationTemplate | None:
    template = (
        NotificationTemplate.objects.filter(event_key=event_key, channel=channel, language=language)
        .order_by("-updated_at")
        .first()
    )
    if template is not None:
        return template
    if language != "en":
        return (
            NotificationTemplate.objects.filter(event_key=event_key, channel=channel, language="en")
            .order_by("-updated_at")
            .first()
        )
    return None


def _render_string(template_source: str, context: dict[str, object]) -> str:
    if not template_source:
        return ""
    return Template(template_source).render(Context(context))


def _default_subject(event: EventType) -> str:
    return event.description


def _default_body(event: EventType, context: dict[str, object]) -> str:
    if context:
        items = sorted(context.items(), key=lambda pair: str(pair[0]))
        details = ", ".join(f"{key}={value}" for key, value in items)
        return f"{event.description} ({details})"
    return event.description
