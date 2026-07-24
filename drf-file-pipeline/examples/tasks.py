"""Wiring process_upload() into Celery. See ``docs/examples.md``.

Requires ``pip install celery`` — not a dependency of this package.
"""

from __future__ import annotations

from celery import shared_task

from drf_file_pipeline.processing import process_upload


@shared_task(bind=True, max_retries=3)
def process_upload_task(self, upload_id: str) -> None:
    try:
        process_upload(upload_id)
    except Exception as exc:
        self.retry(exc=exc, countdown=30)
