"""Django models used by the test suite."""

from __future__ import annotations

from django.db import models


class Payment(models.Model):
    amount = models.IntegerField()
    currency = models.CharField(max_length=3, default="usd")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "test_app"
        ordering = ["id"]
