"""Views used by the test suite.

Tests assert "the view only actually ran once" by checking
``Payment.objects.count()`` after sending the same idempotent request
multiple times — if the view had re-executed, a second ``Payment`` row
would exist.
"""

from __future__ import annotations

from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_idempotency import idempotent
from tests.test_app.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "amount", "currency"]


class CreatePaymentView(APIView):
    """A view protected by the global IdempotencyMiddleware (no decorator needed)."""

    def post(self, request: object) -> Response:
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class FailingPaymentView(APIView):
    """Always raises, to test that failed requests release their lock."""

    def post(self, request: object) -> Response:
        raise RuntimeError("simulated failure")


class ServerErrorPaymentView(APIView):
    """Always returns 500, to test that 5xx responses aren't cached."""

    def post(self, request: object) -> Response:
        return Response({"detail": "internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@idempotent()
def create_payment_decorated(request: object) -> Response:
    serializer = PaymentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payment = serializer.save()
    return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@idempotent()
def failing_payment_decorated(request: object) -> Response:
    raise RuntimeError("simulated failure")
