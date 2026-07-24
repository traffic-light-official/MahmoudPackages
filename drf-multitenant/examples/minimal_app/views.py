"""See ``docs/examples.md``."""

from __future__ import annotations

from examples.minimal_app.models import Project
from examples.minimal_app.serializers import ProjectSerializer
from rest_framework import viewsets

from drf_multitenant.permissions import IsTenantMember


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsTenantMember]
