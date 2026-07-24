"""Tool registration: turning DRF viewsets into callable tool definitions.

The central entry point is the :func:`expose_as_tool` class decorator,
which registers one :class:`ToolDefinition` per requested action into a
:class:`ToolRegistry` (the module-level :data:`default_registry` by
default). Because each ``ToolDefinition`` stores a reference to the
viewset/serializer *classes* rather than a frozen copy of their schema,
regenerating a tool's schema (via :meth:`ToolDefinition.input_json_schema`)
always reflects the current state of the code — there is no separate
"resync" step, which is what makes tool schemas here self-updating.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, TypeVar

from django.core.exceptions import FieldDoesNotExist
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import ViewSetMixin

from drf_llm_gateway.exceptions import ToolRegistrationError
from drf_llm_gateway.naming import viewset_base_name
from drf_llm_gateway.schema import JSONSchema, serializer_to_json_schema
from drf_llm_gateway.settings import get_setting
from drf_llm_gateway.versioning import compute_schema_hash

_V = TypeVar("_V", bound=type)

#: Mapping of standard `ModelViewSet`/`ReadOnlyModelViewSet` action names to
#: ``(http_method, detail)``. Custom ``@action``-decorated methods are
#: introspected via their attached ``.mapping``/``.detail`` attributes
#: instead of this table.
STANDARD_ACTIONS: Mapping[str, tuple[str, bool]] = {
    "list": ("GET", False),
    "create": ("POST", False),
    "retrieve": ("GET", True),
    "update": ("PUT", True),
    "partial_update": ("PATCH", True),
    "destroy": ("DELETE", True),
}


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """A single callable tool derived from one viewset action.

    Attributes:
        name: The unique tool name (see :func:`expose_as_tool`).
        description: Human-readable description shown to the LLM.
        viewset_class: The DRF viewset class this tool dispatches to.
        action: The action name (``"list"``, ``"retrieve"``, a custom
            ``@action`` name, ...).
        http_method: The HTTP method used to dispatch this action.
        detail: Whether this action operates on a single object (``True``)
            or a collection (``False``).
        lookup_field: The URL kwarg name identifying the target object for
            detail actions (ignored for non-detail actions).
        serializer_class: The serializer class describing this action's
            request body, or ``None`` for actions with no body (``list``,
            ``retrieve``, ``destroy``).
        permission_classes: Permission classes enforced by
            :func:`~drf_llm_gateway.executor.execute_tool`.
        authentication_classes: Authentication classes used to resolve the
            calling identity in :func:`~drf_llm_gateway.executor.execute_tool`.
        examples: Example argument payloads, surfaced in generated schemas
            when :ref:`INCLUDE_EXAMPLES_IN_SCHEMA <settings-include-examples-in-schema>`
            is enabled.
        version: Developer-supplied semantic version string (defaults to
            ``"1.0.0"``). Independent of :attr:`schema_hash`, which tracks
            *actual* schema changes automatically.
    """

    name: str
    description: str
    viewset_class: type
    action: str
    http_method: str
    detail: bool
    lookup_field: str
    serializer_class: type[BaseSerializer[Any]] | None
    permission_classes: tuple[type[BasePermission], ...] = ()
    authentication_classes: tuple[type[BaseAuthentication], ...] = ()
    examples: tuple[Mapping[str, Any], ...] = ()
    version: str = "1.0.0"

    def input_json_schema(self) -> JSONSchema:
        """Build the JSON Schema for this tool's callable arguments.

        Returns:
            An object schema combining the detail lookup parameter (for
            detail actions) with the serializer's writable fields (for
            actions with a request body). ``partial_update`` never marks
            fields as required, matching HTTP ``PATCH`` semantics.
        """
        properties: dict[str, JSONSchema] = {}
        required: list[str] = []

        if self.detail:
            properties[self.lookup_field] = self._lookup_field_schema()
            required.append(self.lookup_field)

        if self.serializer_class is not None and self.action in (
            "create",
            "update",
            "partial_update",
        ):
            body_schema = serializer_to_json_schema(self.serializer_class, mode="input")
            properties.update(body_schema.get("properties", {}))
            if self.action != "partial_update":
                required.extend(body_schema.get("required", []))

        schema: JSONSchema = {"type": "object", "properties": properties}
        if required:
            schema["required"] = sorted(set(required))
        if self.examples and get_setting("INCLUDE_EXAMPLES_IN_SCHEMA"):
            schema["examples"] = list(self.examples)
        return schema

    @property
    def schema_hash(self) -> str:
        """A content hash of :meth:`input_json_schema`, for drift detection."""
        return compute_schema_hash(self.input_json_schema())

    def _lookup_field_schema(self) -> JSONSchema:
        """Infer the JSON Schema type of this tool's detail lookup field.

        Inspects the viewset's ``queryset.model`` for a field matching
        :attr:`lookup_field` (typically the primary key, but any model
        field works for a custom ``lookup_field``) to decide between
        ``integer``, ``string`` (UUID), and plain ``string``. Falls back
        to ``integer`` if the model or field can't be determined (e.g. the
        viewset builds its queryset dynamically in ``get_queryset()``).
        """
        model = getattr(getattr(self.viewset_class, "queryset", None), "model", None)
        if model is None:
            return {"type": "integer"}
        try:
            model_field = model._meta.get_field(self.lookup_field)
        except FieldDoesNotExist:
            return {"type": "integer"}
        internal_type = model_field.get_internal_type()
        if internal_type in {"AutoField", "BigAutoField", "SmallAutoField", "IntegerField"}:
            return {"type": "integer"}
        if internal_type == "UUIDField":
            return {"type": "string", "format": "uuid"}
        return {"type": "string"}


class ToolRegistry:
    """An ordered collection of :class:`ToolDefinition` objects.

    Most projects only interact with the module-level
    :data:`default_registry` (via :func:`expose_as_tool`), but a custom
    registry is useful for isolating tool sets in tests or for exposing
    different tool sets to different agent identities.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        """Add a tool definition to the registry.

        Args:
            tool: The tool to register.

        Raises:
            drf_llm_gateway.exceptions.ToolRegistrationError: If a tool
                with the same name is already registered.
        """
        if tool.name in self._tools:
            raise ToolRegistrationError(
                f"A tool named {tool.name!r} is already registered "
                f"(existing: {self._tools[tool.name].viewset_class.__name__}, "
                f"new: {tool.viewset_class.__name__})."
            )
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """Remove a tool definition by name, if present.

        Args:
            name: The tool name to remove. A no-op if not registered.
        """
        self._tools.pop(name, None)

    def get(self, name: str) -> ToolDefinition | None:
        """Look up a tool definition by name.

        Args:
            name: The tool name.

        Returns:
            The matching :class:`ToolDefinition`, or ``None``.
        """
        return self._tools.get(name)

    def __iter__(self) -> Iterator[ToolDefinition]:
        return iter(self._tools.values())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: object) -> bool:
        return name in self._tools

    def clear(self) -> None:
        """Remove every registered tool. Primarily useful in tests."""
        self._tools.clear()


#: The registry :func:`expose_as_tool` registers into unless a different
#: registry is passed explicitly.
default_registry = ToolRegistry()


def expose_as_tool(
    *,
    actions: Sequence[str] = ("list", "retrieve", "create", "update", "partial_update", "destroy"),
    name_prefix: str | None = None,
    descriptions: Mapping[str, str] | None = None,
    serializer_classes: Mapping[str, type[BaseSerializer[Any]]] | None = None,
    examples: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    lookup_field: str | None = None,
    registry: ToolRegistry | None = None,
) -> Callable[[_V], _V]:
    """Register a viewset's actions as tools.

    Args:
        actions: Which actions to expose. Standard actions
            (``"list"``, ``"create"``, ``"retrieve"``, ``"update"``,
            ``"partial_update"``, ``"destroy"``) are recognized
            automatically; custom ``@action``-decorated method names are
            also supported, introspected via their ``.mapping``/``.detail``
            attributes.
        name_prefix: Base name used to build each tool's name, as
            ``f"{name_prefix}{NAME_SEPARATOR}{action}"``. Defaults to a
            snake_case version of the viewset's class name with any
            trailing ``ViewSet``/``APIView``/``View`` suffix stripped
            (e.g. ``ArticleViewSet`` -> ``article``).
        descriptions: Optional per-action description overrides. Actions
            without an override get a generated default description.
        serializer_classes: Optional per-action serializer class
            overrides. Defaults to the viewset's ``serializer_class``
            attribute for every action.
        examples: Optional per-action example argument payloads, surfaced
            in the generated schema.
        lookup_field: URL kwarg name for detail actions. Defaults to the
            viewset's ``lookup_url_kwarg`` or ``lookup_field`` attribute,
            or ``"pk"``.
        registry: The :class:`ToolRegistry` to register into. Defaults to
            :data:`default_registry`.

    Returns:
        A class decorator that registers the tools as a side effect and
        returns the viewset class unchanged.

    Raises:
        drf_llm_gateway.exceptions.ToolRegistrationError: If a resulting
            tool name collides with an already-registered tool, or if an
            action name isn't a standard action and isn't found as an
            ``@action``-decorated method on the viewset.

    Example:
        .. code-block:: python

            @expose_as_tool(actions=["list", "retrieve"])
            class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
                queryset = Article.objects.all()
                serializer_class = ArticleSerializer
    """
    target_registry = registry if registry is not None else default_registry
    descriptions = descriptions or {}
    serializer_classes = serializer_classes or {}
    examples = examples or {}

    def decorator(viewset_class: _V) -> _V:
        base_name = name_prefix or viewset_base_name(viewset_class)
        separator = get_setting("NAME_SEPARATOR")
        resolved_lookup_field = (
            lookup_field
            or getattr(viewset_class, "lookup_url_kwarg", None)
            or getattr(viewset_class, "lookup_field", None)
            or "pk"
        )
        for action_name in actions:
            http_method, detail = _resolve_action(viewset_class, action_name)
            tool = ToolDefinition(
                name=f"{base_name}{separator}{action_name}",
                description=descriptions.get(action_name)
                or _default_description(viewset_class, action_name),
                viewset_class=viewset_class,
                action=action_name,
                http_method=http_method,
                detail=detail,
                lookup_field=resolved_lookup_field,
                serializer_class=serializer_classes.get(
                    action_name, getattr(viewset_class, "serializer_class", None)
                ),
                permission_classes=tuple(getattr(viewset_class, "permission_classes", ())),
                authentication_classes=tuple(getattr(viewset_class, "authentication_classes", ())),
                examples=tuple(examples.get(action_name, ())),
            )
            target_registry.register(tool)
        return viewset_class

    return decorator


def _resolve_action(viewset_class: type, action_name: str) -> tuple[str, bool]:
    if action_name in STANDARD_ACTIONS:
        return STANDARD_ACTIONS[action_name]
    method = getattr(viewset_class, action_name, None)
    mapping = getattr(method, "mapping", None)
    if method is None or mapping is None:
        raise ToolRegistrationError(
            f"{viewset_class.__name__!r} has no standard or @action-decorated "
            f"method named {action_name!r}."
        )
    detail = bool(getattr(method, "detail", False))
    http_method = next(iter(mapping)).upper()
    return http_method, detail


def _default_description(viewset_class: type, action_name: str) -> str:
    if not issubclass(viewset_class, ViewSetMixin):
        raise ToolRegistrationError(
            f"{viewset_class.__name__!r} must be a DRF viewset (subclass of "
            f"rest_framework.viewsets.ViewSetMixin) to use expose_as_tool."
        )
    model = getattr(getattr(viewset_class, "queryset", None), "model", None)
    subject = model.__name__ if model is not None else viewset_class.__name__
    verbs = {
        "list": f"List {subject} objects.",
        "create": f"Create a new {subject}.",
        "retrieve": f"Retrieve a single {subject} by its identifier.",
        "update": f"Replace all fields of a {subject}.",
        "partial_update": f"Update one or more fields of a {subject}.",
        "destroy": f"Delete a {subject}.",
    }
    return verbs.get(action_name, f"Run the {action_name!r} action on {subject}.")
