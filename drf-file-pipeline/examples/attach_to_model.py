"""Attaching an upload to your own model. See ``docs/examples.md``."""

from __future__ import annotations

from django.db import models


class Document(models.Model):
    upload = models.OneToOneField(
        "drf_file_pipeline.FileUpload", on_delete=models.CASCADE, related_name="document"
    )
    title = models.CharField(max_length=200)

    class Meta:
        app_label = "examples"
