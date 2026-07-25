# Quick Start

A complete worked example: a blog API that notifies an author's
subscribers when a new article is published, with a database-backed
template, a webhook target, and quiet hours.

## Register the event type

```python
# blog/apps.py
from django.apps import AppConfig


class BlogConfig(AppConfig):
    name = "blog"

    def ready(self) -> None:
        from drf_notification.constants import CHANNEL_EMAIL, CHANNEL_IN_APP, CHANNEL_WEBHOOK
        from drf_notification.events import register

        register(
            "article.published",
            "A new article was published.",
            default_channels=frozenset({CHANNEL_EMAIL, CHANNEL_IN_APP, CHANNEL_WEBHOOK}),
        )
```

## Send it

```python
# blog/views.py
from rest_framework import viewsets

from blog.models import Article
from blog.serializers import ArticleSerializer
from drf_notification.notify import notify


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def perform_create(self, serializer):
        article = serializer.save()
        for subscriber in article.author.subscribers.all():
            notify(
                recipient=subscriber,
                event_key="article.published",
                context={"title": article.title, "url": article.get_absolute_url()},
            )
```

## Add a template (optional)

Without one, subscribers get a plain default derived from the event
description. With one, via Django admin or a data migration:

```python
from drf_notification.models import NotificationTemplate

NotificationTemplate.objects.create(
    event_key="article.published",
    channel="email",
    subject_template="New post: {{ title }}",
    body_template="{{ title }} was just published. Read it here: {{ url }}",
)
```

## Let subscribers manage their preferences

```python
# urls.py
urlpatterns = [
    path("notifications/", include("drf_notification.urls")),
]
```

A subscriber can now:

- `PATCH /notifications/settings/` with `{"quiet_hours_start": "22:00",
  "quiet_hours_end": "07:00"}` to silence non-urgent notifications
  overnight (they'll get one digest email in the morning instead).
- `POST /notifications/preferences/` with `{"event_key":
  "article.published", "channel": "webhook", "enabled": false}` to turn
  off just the webhook channel for this event.
- `POST /notifications/webhook-targets/` with `{"url":
  "https://example.com/my-webhook"}` to receive a signed HTTP POST for
  every notification instead of (or in addition to) email.

## What subscribers receive

```json
{
  "event": "article.published",
  "subject": "New post: Shipping Faster with Sparse Fieldsets",
  "body": "Shipping Faster with Sparse Fieldsets was just published. Read it here: https://example.com/articles/42/",
  "context": {"title": "Shipping Faster with Sparse Fieldsets", "url": "https://example.com/articles/42/"}
}
```

(For the webhook channel; email/SMS/push render the same `subject`/`body`
through their own backend, and in-app notifications appear via `GET
/notifications/items/`.)

See [Advanced Usage](advanced-usage.md) for custom backends, Celery, and
localized templates.
