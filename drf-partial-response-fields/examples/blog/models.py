"""Example models for the blog API shown in docs/examples.md."""

from __future__ import annotations

from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()


class Tag(models.Model):
    label = models.CharField(max_length=100)


class Article(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="articles")
    tags = models.ManyToManyField(Tag, related_name="articles")
    created_at = models.DateTimeField(auto_now_add=True)


class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
