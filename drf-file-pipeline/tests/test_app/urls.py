"""URLconf used by the test suite."""

from __future__ import annotations

from django.urls import path
from rest_framework.routers import DefaultRouter

from drf_file_pipeline.views import (
    AbortUploadView,
    CompleteUploadView,
    FileUploadViewSet,
    InitiateUploadView,
    PresignPartView,
    ReportPartView,
)

router = DefaultRouter()
router.register("uploads", FileUploadViewSet, basename="fileupload")

urlpatterns = [
    path("uploads/initiate/", InitiateUploadView.as_view(), name="upload-initiate"),
    path("uploads/<uuid:pk>/parts/", ReportPartView.as_view(), name="upload-report-part"),
    path(
        "uploads/<uuid:pk>/parts/<int:part_number>/presign/",
        PresignPartView.as_view(),
        name="upload-presign-part",
    ),
    path("uploads/<uuid:pk>/complete/", CompleteUploadView.as_view(), name="upload-complete"),
    path("uploads/<uuid:pk>/abort/", AbortUploadView.as_view(), name="upload-abort"),
    *router.urls,
]
