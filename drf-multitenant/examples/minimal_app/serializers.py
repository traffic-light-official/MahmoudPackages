"""See ``docs/examples.md``."""

from __future__ import annotations

from examples.minimal_app.models import Project

from drf_multitenant.serializers import TenantScopedModelSerializer


class ProjectSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "tenant", "name"]
        read_only_fields = ["id", "tenant"]
