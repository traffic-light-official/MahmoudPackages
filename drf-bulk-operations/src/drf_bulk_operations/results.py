"""The per-item result shape shared by every bulk operation mixin."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rest_framework import status
from rest_framework.response import Response


@dataclass
class ItemResult:
    """The outcome of processing a single item within a bulk request.

    Attributes:
        index: The item's position (0-based) in the submitted list.
        success: Whether this item validated and saved successfully.
        data: The serialized result, when ``success`` is ``True``. ``None``
            for a successful destroy (there's nothing to serialize).
        errors: The validation errors or failure detail, when ``success``
            is ``False``.
    """

    index: int
    success: bool
    data: Any | None = None
    errors: Any | None = None

    def as_dict(self) -> dict[str, Any]:
        """Render as the per-item dict used in a 207/400 response body."""
        result: dict[str, Any] = {
            "index": self.index,
            "status": "success" if self.success else "error",
        }
        if self.success:
            result["data"] = self.data
        else:
            result["errors"] = self.errors
        return result


def build_bulk_response(
    results: list[ItemResult],
    *,
    all_success_status: int,
    empty_success_body: bool = False,
) -> Response:
    """Build the HTTP response for a completed non-atomic bulk operation.

    - Every item succeeded: ``all_success_status`` with a plain list of
      each item's ``data`` (or no body at all, if ``empty_success_body``).
    - Some but not all succeeded: ``207 Multi-Status`` with a list of
      per-item ``{"index", "status", "data"|"errors"}`` dicts.
    - Every item failed: ``400 Bad Request`` with the same per-item shape.
    """
    if all(result.success for result in results):
        if empty_success_body:
            return Response(status=all_success_status)
        return Response([result.data for result in results], status=all_success_status)
    if any(result.success for result in results):
        return Response(
            [result.as_dict() for result in results], status=status.HTTP_207_MULTI_STATUS
        )
    return Response([result.as_dict() for result in results], status=status.HTTP_400_BAD_REQUEST)
