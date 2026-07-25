"""Minimal models for exercising object-level permission checks."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=200)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        app_label = "test_app"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.title
