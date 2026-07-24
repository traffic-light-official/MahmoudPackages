"""A minimal tenant-scoped Django app, illustrating the core setup.

Not wired into this package's own test suite (see ``tests/test_app``
for that) — this is documentation-as-code, referenced from
``docs/examples.md``.
"""

from __future__ import annotations

from django.db import models

from drf_multitenant.models import TenantScopedModel


class Tenant(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)


class Project(TenantScopedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    archived = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
