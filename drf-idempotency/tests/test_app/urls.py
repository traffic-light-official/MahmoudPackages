"""URL configuration for the test suite's Django project."""

from __future__ import annotations

from django.urls import path

from tests.test_app.views import (
    CreatePaymentView,
    FailingPaymentView,
    ServerErrorPaymentView,
    create_payment_decorated,
    failing_payment_decorated,
)

urlpatterns = [
    path("payments/", CreatePaymentView.as_view(), name="create-payment"),
    path("payments-decorated/", create_payment_decorated, name="create-payment-decorated"),
    path("payments-failing/", FailingPaymentView.as_view(), name="create-payment-failing"),
    path(
        "payments-failing-decorated/",
        failing_payment_decorated,
        name="create-payment-failing-decorated",
    ),
    path("payments-500/", ServerErrorPaymentView.as_view(), name="create-payment-500"),
]
