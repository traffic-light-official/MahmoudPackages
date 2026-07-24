"""Django models used by the test suite."""

from __future__ import annotations

from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()

    class Meta:
        app_label = "test_app"
        ordering = ["id"]


class Tag(models.Model):
    label = models.CharField(max_length=100)

    class Meta:
        app_label = "test_app"
        ordering = ["id"]


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=255)
    body = models.TextField(blank=True, default="")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="articles")
    tags = models.ManyToManyField(Tag, related_name="articles", blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    view_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "test_app"
        ordering = ["id"]
