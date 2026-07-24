"""Views used by the test suite."""

from __future__ import annotations

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_ratelimit_plus import RateLimitHeadersMixin, rate_limit, ratelimit


class TokenBucketView(RateLimitHeadersMixin, APIView):
    throttle_classes = [rate_limit(rate="5/m", algorithm="token_bucket", burst=5, key="ip")]

    def get(self, request: object) -> Response:
        return Response({"ok": True})


class FixedWindowView(RateLimitHeadersMixin, APIView):
    throttle_classes = [rate_limit(rate="5/m", algorithm="fixed_window", key="ip")]

    def get(self, request: object) -> Response:
        return Response({"ok": True})


class SlidingWindowView(RateLimitHeadersMixin, APIView):
    throttle_classes = [rate_limit(rate="5/m", algorithm="sliding_window", key="ip")]

    def get(self, request: object) -> Response:
        return Response({"ok": True})


class WeightedCostView(RateLimitHeadersMixin, APIView):
    throttle_classes = [
        rate_limit(rate="10/m", algorithm="token_bucket", burst=10, key="ip", cost=3)
    ]

    def get(self, request: object) -> Response:
        return Response({"ok": True})


class PerUserView(RateLimitHeadersMixin, APIView):
    throttle_classes = [rate_limit(rate="5/m", algorithm="token_bucket", burst=5, key="user")]

    def get(self, request: object) -> Response:
        return Response({"ok": True})


class TierView(RateLimitHeadersMixin, APIView):
    throttle_classes = [
        rate_limit(
            rate={"free": "2/m", "pro": "10/m"},
            algorithm="token_bucket",
            key="user",
        )
    ]

    def get(self, request: object) -> Response:
        return Response({"ok": True})


@api_view(["GET"])
@ratelimit(rate="3/m", algorithm="token_bucket", burst=3, key="ip")
def decorated_view(request: object) -> Response:
    return Response({"ok": True})
