"""Example app config registering an event type, shown in docs/quickstart.md."""

from __future__ import annotations

from django.apps import AppConfig


class BlogConfig(AppConfig):
    name = "examples.blog"
    label = "examples_blog"

    def ready(self) -> None:
        from drf_notification.constants import CHANNEL_EMAIL, CHANNEL_IN_APP, CHANNEL_WEBHOOK
        from drf_notification.events import register

        register(
            "article.published",
            "A new article was published.",
            default_channels=frozenset({CHANNEL_EMAIL, CHANNEL_IN_APP, CHANNEL_WEBHOOK}),
        )
