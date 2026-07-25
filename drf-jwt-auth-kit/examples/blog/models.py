"""Example models for the blog API shown in docs/quickstart.md."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="articles"
    )
