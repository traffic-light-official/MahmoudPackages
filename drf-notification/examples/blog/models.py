"""Example models for the blog API shown in docs/quickstart.md."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class Author(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subscribers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="subscribed_authors"
    )


class Article(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="articles")

    def get_absolute_url(self) -> str:
        return f"/articles/{self.pk}/"
