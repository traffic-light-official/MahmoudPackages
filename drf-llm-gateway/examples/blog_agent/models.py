"""Example models for the blog agent backend shown in docs/examples.md."""

from __future__ import annotations

from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=255)
    body = models.TextField(blank=True, default="")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="articles")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
