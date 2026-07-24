"""Shared constants used across the package's public modules."""

from __future__ import annotations

from typing import Final

#: Key under which the parsed :class:`~drf_partial_response_fields.tree.FieldTree`
#: for the *current request* is stored in a DRF serializer context dict.
#: :class:`~drf_partial_response_fields.mixins.PartialResponseMixin` sets
#: this automatically; plain :class:`~rest_framework.views.APIView`
#: subclasses that build serializers manually should set it themselves,
#: see ``docs/advanced-usage.md``.
CONTEXT_KEY: Final[str] = "_partial_response_fields_tree"
