"""Minimal models for exercising real N+1 query patterns in tests."""

from __future__ import annotations

from django.db import models


class Author(models.Model):
    """An article's author - the "one" side of the N+1 pattern under test."""

    name = models.CharField(max_length=200)

    class Meta:
        app_label = "test_app"

    def __str__(self) -> str:
        return self.name


class Article(models.Model):
    """An article, with a required FK to :class:`Author`.

    Iterating ``Article.objects.all()`` and accessing ``.author.name`` on
    each row is the textbook N+1: one query for the articles, then one
    additional query per row for its author, unless ``select_related``
    is used.
    """

    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="articles")

    class Meta:
        app_label = "test_app"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.title
