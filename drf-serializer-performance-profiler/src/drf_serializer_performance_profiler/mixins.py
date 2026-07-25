"""``ProfileSerializerMixin``/``ProfileSerializerViewMixin``: per-field timing and query counts.

Mix :class:`ProfileSerializerMixin` into a serializer to record every
field's timing/query count; mix
:class:`ProfileSerializerViewMixin` into the view/viewset that uses it
to expose the aggregated result as a response header. The serializer
mixin's ``to_representation`` is a line-for-line copy of DRF's own
``Serializer.to_representation`` with measurement inserted around each
field - it never changes what gets serialized, only what gets recorded
alongside it.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from rest_framework.fields import SkipField
from rest_framework.relations import PKOnlyObject

from drf_serializer_performance_profiler.profiling import (
    SerializerProfile,
    get_serializer_profile,
    measure,
    merge_profiles,
)
from drf_serializer_performance_profiler.settings import get_setting

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.response import Response

logger = logging.getLogger("drf_serializer_performance_profiler")


def _is_profiling_authorized(request: Request) -> bool:
    if not get_setting("ENABLED"):
        return False
    if not get_setting("RESTRICT_TO_STAFF"):
        return True
    user = getattr(request, "user", None)
    return bool(user and user.is_authenticated and user.is_staff)


class ProfileSerializerMixin:
    """Records per-field timing and query counts every time this serializer runs.

    Instrumentation only runs when the ``SERIALIZER_PROFILER`` setting's
    ``ENABLED`` or ``LOG_SLOW_FIELDS`` is ``True`` - with both ``False``
    (the default), ``to_representation`` delegates straight to
    ``super()`` with no measurement overhead at all.
    """

    def to_representation(self, instance: Any) -> Any:
        """Same output as the wrapped serializer's own ``to_representation``, plus profiling."""
        if not get_setting("ENABLED") and not get_setting("LOG_SLOW_FIELDS"):
            return super().to_representation(instance)  # type: ignore[misc]

        ret: dict[str, Any] = {}
        fields = self._readable_fields  # type: ignore[attr-defined]
        profile = get_serializer_profile(self) or SerializerProfile()  # type: ignore[arg-type]
        self._serializer_profile = profile
        threshold_ms = get_setting("SLOW_FIELD_THRESHOLD_MS")
        log_slow_fields = get_setting("LOG_SLOW_FIELDS")

        for read_field in fields:
            with measure() as measurement:
                try:
                    attribute = read_field.get_attribute(instance)
                except SkipField:
                    continue
                check_for_none = attribute.pk if isinstance(attribute, PKOnlyObject) else attribute
                if check_for_none is None:
                    ret[read_field.field_name] = None
                else:
                    ret[read_field.field_name] = read_field.to_representation(attribute)
            profile.record(read_field.field_name, measurement.elapsed_ms, measurement.query_count)
            if log_slow_fields and measurement.elapsed_ms >= threshold_ms:
                logger.warning(
                    "Slow serializer field %s.%s: %.2fms (%d quer%s)",
                    type(self).__name__,
                    read_field.field_name,
                    measurement.elapsed_ms,
                    measurement.query_count,
                    "y" if measurement.query_count == 1 else "ies",
                )

        return ret


class ProfileSerializerViewMixin:
    """Attaches an aggregated serializer profile to the response, if authorized.

    Mix into a ``GenericAPIView``/viewset that uses a
    :class:`ProfileSerializerMixin`-based serializer - captures every
    serializer instance created via ``get_serializer()`` during the
    request, merges their profiles, and (only when the
    ``SERIALIZER_PROFILER`` setting authorizes it) attaches the merged
    result as a response header.
    """

    def get_serializer(self, *args: Any, **kwargs: Any) -> Any:
        """Capture the created serializer instance for later profiling."""
        serializer = super().get_serializer(*args, **kwargs)  # type: ignore[misc]
        captured: list[Any] | None = getattr(self, "_profiled_serializers", None)
        if captured is None:
            captured = []
            self._profiled_serializers = captured
        captured.append(serializer)
        return serializer

    def finalize_response(
        self, request: Request, response: Response, *args: Any, **kwargs: Any
    ) -> Response:
        """Attach the merged serializer profile to the response, if authorized."""
        response = super().finalize_response(  # type: ignore[misc]
            request, response, *args, **kwargs
        )
        if not _is_profiling_authorized(request):
            return response

        captured: list[Any] = getattr(self, "_profiled_serializers", [])
        profiles: list[SerializerProfile] = []
        for serializer in captured:
            # A `many=True` serializer is a `ListSerializer` wrapping this
            # package's mixin on its `.child` - the profile accumulates on
            # the child (since `ListSerializer.to_representation` calls
            # `self.child.to_representation(item)` per row), not on the
            # `ListSerializer` instance `get_serializer()` actually returns.
            profile = get_serializer_profile(serializer) or get_serializer_profile(
                getattr(serializer, "child", None)
            )
            if profile is not None:
                profiles.append(profile)
        if not profiles:
            return response

        merged = merge_profiles(profiles)
        response[get_setting("HEADER_NAME")] = merged.as_header_value()
        return response
