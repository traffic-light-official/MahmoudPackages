"""Minimal models used by the test suite to exercise nested serializer errors."""

from __future__ import annotations

from django.db import models


class Author(models.Model):
    """A blog post author."""

    name = models.CharField(max_length=100)
    email = models.EmailField()

    class Meta:
        app_label = "test_app"

    def __str__(self) -> str:
        return self.name


class Article(models.Model):
    """A blog post, written by exactly one :class:`Author`."""

    title = models.CharField(max_length=200)
    body = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="articles")

    class Meta:
        app_label = "test_app"

    def __str__(self) -> str:
        return self.title
