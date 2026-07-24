"""Django models used by the test suite."""

from __future__ import annotations

from django.db import models

from drf_multitenant.models import TenantScopedModel


class Tenant(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        app_label = "test_app"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name


class Author(TenantScopedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="authors")
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "test_app"
        ordering = ["id"]


class Article(TenantScopedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="articles")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="articles")
    title = models.CharField(max_length=200)

    class Meta:
        app_label = "test_app"
        ordering = ["id"]
