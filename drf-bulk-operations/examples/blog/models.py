"""Minimal models for the runnable example."""

from __future__ import annotations

from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        app_label = "blog"

    def __str__(self) -> str:
        return self.name


class Article(models.Model):
    title = models.CharField(max_length=200, unique=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="articles")
    published = models.BooleanField(default=False)

    class Meta:
        app_label = "blog"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.title
