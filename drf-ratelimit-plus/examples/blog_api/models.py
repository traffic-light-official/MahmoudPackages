"""Example model for the tiered blog API shown in docs/examples.md."""

from __future__ import annotations

from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True, default="")
