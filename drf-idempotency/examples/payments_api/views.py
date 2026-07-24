"""Example view for the payments API shown in docs/examples.md."""

from __future__ import annotations

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from examples.payments_api.serializers import PaymentSerializer


class CreatePaymentView(APIView):
    """Protected by the project-wide ``IdempotencyMiddleware``."""

    def post(self, request: Request) -> Response:
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
