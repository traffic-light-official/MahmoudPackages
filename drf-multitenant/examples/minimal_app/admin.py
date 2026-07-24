"""See ``docs/examples.md``."""

from __future__ import annotations

from django.contrib import admin
from examples.minimal_app.models import Project

from drf_multitenant.admin import TenantAdminMixin


@admin.register(Project)
class ProjectAdmin(TenantAdminMixin):
    list_display = ["name", "tenant"]
