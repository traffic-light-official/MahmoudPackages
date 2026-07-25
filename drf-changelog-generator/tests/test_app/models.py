"""A minimal model exposed via DRF so drf-spectacular has a real schema to generate."""

from __future__ import annotations

from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()

    class Meta:
        app_label = "test_app"
