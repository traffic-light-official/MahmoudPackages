# Examples

Runnable versions live in
[`examples/`](https://github.com/mahmoudgshaker/drf-idempotency/tree/main/examples).

## A payments API

```python
# models.py
from django.db import models


class Payment(models.Model):
    amount = models.IntegerField()
    currency = models.CharField(max_length=3, default="usd")
    created_at = models.DateTimeField(auto_now_add=True)
```

```python
# serializers.py
from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "amount", "currency", "created_at"]
```

```python
# views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Payment
from .serializers import PaymentSerializer


class CreatePaymentView(APIView):
    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
```

```python
# settings.py
MIDDLEWARE = [..., "drf_idempotency.middleware.IdempotencyMiddleware"]
IDEMPOTENCY = {"BACKEND": "drf_idempotency.backends.database.DatabaseBackend"}
```

### Client-side retry logic

```python
import requests
import uuid

idempotency_key = str(uuid.uuid4())


def create_payment(amount, currency="usd", retries=3):
    for attempt in range(retries):
        try:
            response = requests.post(
                "https://api.example.com/payments/",
                json={"amount": amount, "currency": currency},
                headers={"Idempotency-Key": idempotency_key},
                timeout=5,
            )
            return response.json()
        except requests.exceptions.Timeout:
            if attempt == retries - 1:
                raise
            # Safe to retry with the SAME key - it's the same idempotency_key
            # variable, generated once, outside the loop.
            continue
```

The key point: `idempotency_key` is generated **once**, outside the retry
loop. Generating a new key per attempt would defeat the entire purpose.

## Per-view opt-in instead of global middleware

```python
from rest_framework.decorators import api_view
from drf_idempotency import idempotent


@api_view(["POST"])
@idempotent()
def create_payment(request):
    serializer = PaymentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payment = serializer.save()
    return Response(PaymentSerializer(payment).data, status=201)
```

## Checking status without resending the request

```python
from drf_idempotency import get_idempotency_status
from rest_framework.views import APIView
from rest_framework.response import Response


class PaymentStatusView(APIView):
    def get(self, request, key):
        status_value = get_idempotency_status(key)
        if status_value is None:
            return Response({"detail": "Unknown key"}, status=404)
        return Response({"key": key, "status": status_value})
```
