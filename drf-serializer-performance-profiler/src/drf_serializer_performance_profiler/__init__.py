"""Find slow fields in Django REST Framework serializers.

A slow API endpoint is often a slow *serializer*, not a slow view or a
slow query in isolation - a single ``SerializerMethodField`` computing
an aggregate, or a related field silently triggering a query per row,
can dominate response time while every other field is instant. DRF
gives you no built-in way to see which field is responsible.

:class:`~drf_serializer_performance_profiler.mixins.ProfileSerializerMixin`
instruments each field's ``get_attribute()``/``to_representation()``
individually - timing it and counting the database queries it
triggers, aggregated across every row in a list response - without
changing a single byte of the actual serialized output.
:class:`~drf_serializer_performance_profiler.mixins.ProfileSerializerViewMixin`
exposes the aggregated result as an opt-in, staff-restricted response
header.
"""

from __future__ import annotations

from drf_serializer_performance_profiler.mixins import (
    ProfileSerializerMixin,
    ProfileSerializerViewMixin,
)
from drf_serializer_performance_profiler.profiling import (
    FieldProfile,
    SerializerProfile,
    get_serializer_profile,
    merge_profiles,
)
from drf_serializer_performance_profiler.settings import get_setting

__version__ = "1.0.0"

__all__ = [
    "FieldProfile",
    "ProfileSerializerMixin",
    "ProfileSerializerViewMixin",
    "SerializerProfile",
    "__version__",
    "get_serializer_profile",
    "get_setting",
    "merge_profiles",
]
