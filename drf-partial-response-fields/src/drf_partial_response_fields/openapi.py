"""Optional OpenAPI (drf-spectacular) integration.

Nothing in the rest of this package imports this module, and nothing here
is imported unless you use it: install the ``openapi`` extra
(``pip install drf-partial-response-fields[openapi]``) and either apply
:func:`fields_query_parameter` manually with ``@extend_schema``, or set
``schema = PartialResponseAutoSchema()`` on a view that also uses
:class:`~drf_partial_response_fields.mixins.PartialResponseMixin` to have
the ``fields`` parameter documented automatically.
"""

from __future__ import annotations

from typing import Any

from drf_partial_response_fields.settings import get_setting

try:
    from drf_spectacular.openapi import AutoSchema as _SpectacularAutoSchema
    from drf_spectacular.utils import OpenApiParameter
except ImportError as exc:  # pragma: no cover - exercised via test skip
    raise ImportError(
        "drf_partial_response_fields.openapi requires drf-spectacular. "
        "Install it with: pip install drf-partial-response-fields[openapi]"
    ) from exc


def fields_query_parameter(*, description: str | None = None) -> OpenApiParameter:
    """Build an :class:`~drf_spectacular.utils.OpenApiParameter` for ``fields``.

    Args:
        description: Custom description text. Defaults to a general
            explanation of the sparse-fieldset syntax.

    Returns:
        An ``OpenApiParameter`` describing the configured ``QUERY_PARAM``
        setting, suitable for passing to ``@extend_schema(parameters=[...])``.

    Example:
        .. code-block:: python

            from drf_spectacular.utils import extend_schema
            from drf_partial_response_fields.openapi import fields_query_parameter


            @extend_schema(parameters=[fields_query_parameter()])
            class ArticleViewSet(PartialResponseMixin, viewsets.ModelViewSet):
                ...
    """
    param_name = get_setting("QUERY_PARAM")
    return OpenApiParameter(
        name=param_name,
        type=str,
        location=OpenApiParameter.QUERY,
        required=False,
        description=description
        or (
            "Comma-separated list of fields to include in the response, "
            "e.g. 'id,name'. Supports nested selection with parentheses "
            "(e.g. 'author(name,email)'), exclusion with a '-' prefix "
            "(e.g. '-internal_notes'), and renaming with 'alias:field'. "
            "Omit to receive the full default representation."
        ),
    )


class PartialResponseAutoSchema(_SpectacularAutoSchema):
    """A drf-spectacular ``AutoSchema`` that documents ``?fields=`` automatically.

    Assign this to a view's ``schema`` attribute (or set it as the project
    default via ``SPECTACULAR_SETTINGS["DEFAULT_GENERATOR_CLASS"]`` /
    per-view ``schema =``) to have the ``fields`` query parameter appear in
    the generated OpenAPI schema for every action, without repeating
    ``@extend_schema`` on each view.
    """

    def get_override_parameters(self) -> list[Any]:
        """Return drf-spectacular's normal override parameters plus ``fields``.

        Returns:
            The list of parameters from the parent implementation with a
            :func:`fields_query_parameter` appended.
        """
        params = list(super().get_override_parameters())
        params.append(fields_query_parameter())
        return params
