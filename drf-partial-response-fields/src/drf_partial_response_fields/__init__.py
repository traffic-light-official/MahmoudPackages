"""GraphQL-like sparse fieldsets and automatic query optimization for DRF.

The public API is intentionally small. Most projects only need:

* :class:`~drf_partial_response_fields.serializers.PartialFieldsSerializerMixin`
  (or the ready-made :class:`~drf_partial_response_fields.serializers.PartialFieldsModelSerializer`)
  on every serializer that should honor ``?fields=``.
* :class:`~drf_partial_response_fields.mixins.PartialResponseMixin` on every
  view/viewset that should expose ``?fields=`` and get automatic query
  optimization.
* :func:`~drf_partial_response_fields.decorators.requires_related` on any
  :class:`~rest_framework.serializers.SerializerMethodField` that needs
  extra relations loaded.

See ``docs/quickstart.md`` for a complete end-to-end example.
"""

from __future__ import annotations

from drf_partial_response_fields.decorators import OptimizationHints, requires_related
from drf_partial_response_fields.exceptions import (
    InvalidFieldsParameterError,
    PartialResponseFieldsError,
    UnknownFieldError,
)
from drf_partial_response_fields.mixins import (
    PARTIAL_RESPONSE_FIELDS_CONTEXT_KEY,
    PartialResponseMixin,
    parse_request_fields,
)
from drf_partial_response_fields.optimizer import optimize_queryset
from drf_partial_response_fields.parser import parse_fields
from drf_partial_response_fields.serializers import (
    PartialFieldsListSerializer,
    PartialFieldsModelSerializer,
    PartialFieldsSerializer,
    PartialFieldsSerializerMixin,
)
from drf_partial_response_fields.tree import ALL_TREE, FieldSpec, FieldTree

__version__ = "1.0.0"

__all__ = [
    "ALL_TREE",
    "PARTIAL_RESPONSE_FIELDS_CONTEXT_KEY",
    "FieldSpec",
    "FieldTree",
    "InvalidFieldsParameterError",
    "OptimizationHints",
    "PartialFieldsListSerializer",
    "PartialFieldsModelSerializer",
    "PartialFieldsSerializer",
    "PartialFieldsSerializerMixin",
    "PartialResponseFieldsError",
    "PartialResponseMixin",
    "UnknownFieldError",
    "__version__",
    "optimize_queryset",
    "parse_fields",
    "parse_request_fields",
    "requires_related",
]
