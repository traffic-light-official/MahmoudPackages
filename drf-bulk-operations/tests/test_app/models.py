"""Minimal models for exercising real bulk create/update/destroy operations."""

from __future__ import annotations

from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        app_label = "test_app"

    def __str__(self) -> str:
        return self.name


class Article(models.Model):
    title = models.CharField(max_length=200, unique=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="articles")
    published = models.BooleanField(default=False)

    class Meta:
        app_label = "test_app"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.title
