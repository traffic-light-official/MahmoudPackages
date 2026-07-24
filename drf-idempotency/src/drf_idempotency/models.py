"""Django model backing :class:`drf_idempotency.backends.database.DatabaseBackend`.

This model is only ever written to by :class:`DatabaseBackend`. If your
project uses the Redis backend exclusively, the table still exists (once
migrated) but remains empty and unused — there is no harm in having both
available.
"""

from __future__ import annotations

from django.db import models


class IdempotencyRecord(models.Model):
    """A single idempotency key's stored state and (eventually) response.

    Attributes:
        key: The client-supplied idempotency key. Unique — this uniqueness
            constraint is exactly what makes concurrent lock acquisition
            race-safe (see ``docs/architecture.md``).
        fingerprint: A SHA-256 hex digest of the request method, path, and
            body, computed by :func:`drf_idempotency.fingerprint.compute_fingerprint`.
            Used to detect a key being reused with a different request.
        status: One of ``"in_progress"``, ``"completed"``, or ``"failed"``.
        response_status_code: The HTTP status code of the stored response,
            once completed.
        response_headers: The stored response headers, as a JSON object.
        response_body: The stored response body, base64-encoded (so
            binary bodies round-trip safely through a text column).
        created_at: When this record was first created (lock acquired).
        completed_at: When the response was stored, if it has been.
        expires_at: When this record should be treated as gone. Rows past
            this timestamp are ignored by reads and removed by the
            ``cleanup_expired_idempotency_keys`` management command.
    """

    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = (
        (STATUS_IN_PROGRESS, "In progress"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    )

    key = models.CharField(max_length=255, unique=True)
    fingerprint = models.CharField(max_length=64)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS)
    response_status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    response_headers = models.JSONField(default=dict, blank=True)
    response_body = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        app_label = "drf_idempotency"
        indexes = [models.Index(fields=["expires_at"])]

    def __str__(self) -> str:  # pragma: no cover - debugging aid only
        return f"{self.key} ({self.status})"
