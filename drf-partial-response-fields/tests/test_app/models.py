"""Django models used by the test suite.

These models intentionally cover every relation shape the optimizer needs
to handle: forward FK (``Article.author``), reverse FK (``Author.articles``
/ ``Article.comments``), forward O2O (n/a here, see reverse below), reverse
O2O (``Author.profile``), and M2M (``Article.tags``).
"""

from __future__ import annotations

from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    bio = models.TextField(blank=True, default="")

    class Meta:
        app_label = "test_app"
        ordering = ["id"]

    def __str__(self) -> str:  # pragma: no cover - debugging aid only
        return self.name


class Profile(models.Model):
    author = models.OneToOneField(Author, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=200)
    avatar_url = models.URLField(blank=True, default="")

    class Meta:
        app_label = "test_app"
        ordering = ["id"]


class Tag(models.Model):
    label = models.CharField(max_length=100)

    class Meta:
        app_label = "test_app"
        ordering = ["id"]

    def __str__(self) -> str:  # pragma: no cover - debugging aid only
        return self.label


class Article(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True, default="")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="articles")
    tags = models.ManyToManyField(Tag, related_name="articles", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    view_count = models.IntegerField(default=0)

    class Meta:
        app_label = "test_app"
        ordering = ["id"]

    def __str__(self) -> str:  # pragma: no cover - debugging aid only
        return self.title


class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="comments")
    author_name = models.CharField(max_length=200)
    text = models.TextField()

    class Meta:
        app_label = "test_app"
        ordering = ["id"]
