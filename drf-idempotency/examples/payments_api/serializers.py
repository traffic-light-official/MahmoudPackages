"""Example serializer for the payments API shown in docs/examples.md."""

from __future__ import annotations

from rest_framework import serializers

from examples.payments_api.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "amount", "currency", "created_at"]
        read_only_fields = ["id", "created_at"]
