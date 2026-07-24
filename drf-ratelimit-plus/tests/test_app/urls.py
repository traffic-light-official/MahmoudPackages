"""URL configuration for the test suite's Django project."""

from __future__ import annotations

from django.urls import path

from tests.test_app.views import (
    FixedWindowView,
    PerUserView,
    SlidingWindowView,
    TierView,
    TokenBucketView,
    WeightedCostView,
    decorated_view,
)

urlpatterns = [
    path("token-bucket/", TokenBucketView.as_view(), name="token-bucket"),
    path("fixed-window/", FixedWindowView.as_view(), name="fixed-window"),
    path("sliding-window/", SlidingWindowView.as_view(), name="sliding-window"),
    path("weighted-cost/", WeightedCostView.as_view(), name="weighted-cost"),
    path("per-user/", PerUserView.as_view(), name="per-user"),
    path("tier/", TierView.as_view(), name="tier"),
    path("decorated/", decorated_view, name="decorated"),
]
