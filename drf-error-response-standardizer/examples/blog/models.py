"""Example models for the blog API shown in docs/quickstart.md."""

from __future__ import annotations

from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()


class Article(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="articles")
    published = models.BooleanField(default=False)
