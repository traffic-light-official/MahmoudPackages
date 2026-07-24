"""Extensible registry mapping exception classes to problem types.

The registry is the extension point for "custom exception mapping": any
application can call :func:`register` (fixed title/status/code) or
:func:`register_builder` (full control over the resulting
:class:`~drf_error_response_standardizer.problem.ProblemDetail`) for its own
exception classes, and
:func:`~drf_error_response_standardizer.handler.problem_details_exception_handler`
will pick up the mapping automatically.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import exceptions as drf_exceptions

from drf_error_response_standardizer.codes import BUILTIN_ERROR_TYPES, ErrorType

if TYPE_CHECKING:
    from drf_error_response_standardizer.problem import ProblemDetail

_T = TypeVar("_T")

#: Signature of a custom problem builder: receives the raised exception
#: instance and returns a fully-formed
#: :class:`~drf_error_response_standardizer.problem.ProblemDetail`. Register
#: one via :meth:`ProblemRegistry.register_builder` when a fixed
#: :class:`~drf_error_response_standardizer.codes.ErrorType` is not
#: expressive enough (e.g. the ``detail`` or an extension member must be
#: derived from the exception instance itself).
ProblemBuilder = Callable[[Exception], "ProblemDetail"]


class ProblemRegistry:
    """Maps exception classes to :class:`ErrorType` entries or custom builders.

    Lookups walk the raised exception's method resolution order (MRO), so
    registering a mapping for a base class also covers subclasses with no
    more specific registration of their own - the same resolution strategy
    Django REST Framework uses internally for ``APIException`` subclasses.
    More specific registrations (subclasses) always win over less specific
    ones (base classes) because the MRO is walked from the exact type
    outward.
    """

    def __init__(self) -> None:
        self._error_types: dict[type[Exception], ErrorType] = {}
        self._builders: dict[type[Exception], ProblemBuilder] = {}

    def register(self, exc_class: type[Exception], error_type: ErrorType) -> None:
        """Register a fixed :class:`ErrorType` for ``exc_class`` and its subclasses.

        Args:
            exc_class: The exception class to match.
            error_type: The :class:`ErrorType` used to build the problem's
                ``title``, ``code``, ``status``, and type ``slug``.
        """
        self._error_types[exc_class] = error_type

    def register_builder(self, exc_class: type[Exception], builder: ProblemBuilder) -> None:
        """Register a custom builder callable for ``exc_class`` and its subclasses.

        A registered builder takes precedence over a registered
        :class:`ErrorType` for the same or a more specific exception class.

        Args:
            exc_class: The exception class to match.
            builder: Callable receiving the exception instance and
                returning a complete
                :class:`~drf_error_response_standardizer.problem.ProblemDetail`.
        """
        self._builders[exc_class] = builder

    def unregister(self, exc_class: type[Exception]) -> None:
        """Remove any builder and/or error-type registration for ``exc_class``.

        Primarily useful for tests that need to reset registry state
        between cases.
        """
        self._error_types.pop(exc_class, None)
        self._builders.pop(exc_class, None)

    def find_builder(self, exc: Exception) -> ProblemBuilder | None:
        """Return the most specific registered builder for ``exc``, if any."""
        return self._lookup(exc, self._builders)

    def find_error_type(self, exc: Exception) -> ErrorType | None:
        """Return the most specific registered :class:`ErrorType` for ``exc``, if any."""
        return self._lookup(exc, self._error_types)

    def all_error_types(self) -> list[ErrorType]:
        """Return every distinct :class:`ErrorType` currently registered.

        Used by :mod:`~drf_error_response_standardizer.catalog` to enumerate
        all problem types an API can return.
        """
        seen: dict[str, ErrorType] = {}
        for error_type in self._error_types.values():
            seen[error_type.code] = error_type
        return list(seen.values())

    @staticmethod
    def _lookup(exc: Exception, table: dict[type[Exception], _T]) -> _T | None:
        for klass in type(exc).__mro__:
            if klass in table:
                return table[klass]
        return None


#: The registry used by default throughout the package. Applications may
#: use this instance directly or construct their own
#: :class:`ProblemRegistry` and pass it explicitly to
#: :func:`~drf_error_response_standardizer.handler.problem_details_exception_handler`.
default_registry = ProblemRegistry()

default_registry.register(drf_exceptions.ParseError, BUILTIN_ERROR_TYPES["parse_error"])
default_registry.register(drf_exceptions.NotAuthenticated, BUILTIN_ERROR_TYPES["not_authenticated"])
default_registry.register(
    drf_exceptions.AuthenticationFailed, BUILTIN_ERROR_TYPES["authentication_failed"]
)
default_registry.register(drf_exceptions.PermissionDenied, BUILTIN_ERROR_TYPES["permission_denied"])
default_registry.register(DjangoPermissionDenied, BUILTIN_ERROR_TYPES["permission_denied"])
default_registry.register(drf_exceptions.NotFound, BUILTIN_ERROR_TYPES["not_found"])
default_registry.register(Http404, BUILTIN_ERROR_TYPES["not_found"])
default_registry.register(
    drf_exceptions.MethodNotAllowed, BUILTIN_ERROR_TYPES["method_not_allowed"]
)
default_registry.register(drf_exceptions.NotAcceptable, BUILTIN_ERROR_TYPES["not_acceptable"])
default_registry.register(
    drf_exceptions.UnsupportedMediaType, BUILTIN_ERROR_TYPES["unsupported_media_type"]
)
default_registry.register(drf_exceptions.Throttled, BUILTIN_ERROR_TYPES["throttled"])
default_registry.register(drf_exceptions.ValidationError, BUILTIN_ERROR_TYPES["validation_error"])


def register(exc_class: type[Exception], error_type: ErrorType) -> None:
    """Register a fixed :class:`ErrorType` for ``exc_class`` on the default registry.

    Args:
        exc_class: The exception class to match (and its subclasses).
        error_type: The :class:`ErrorType` to use for this exception class.

    Example:
        .. code-block:: python

            from drf_error_response_standardizer.codes import ErrorType
            from drf_error_response_standardizer.registry import register


            class OutOfStockError(Exception):
                pass


            register(
                OutOfStockError,
                ErrorType(
                    code="out_of_stock",
                    title="Item Out of Stock",
                    slug="out-of-stock",
                    status=409,
                ),
            )
    """
    default_registry.register(exc_class, error_type)


def register_builder(exc_class: type[Exception], builder: ProblemBuilder) -> None:
    """Register a custom builder for ``exc_class`` on the default registry.

    Args:
        exc_class: The exception class to match (and its subclasses).
        builder: Callable receiving the exception instance and returning a
            complete :class:`~drf_error_response_standardizer.problem.ProblemDetail`.
    """
    default_registry.register_builder(exc_class, builder)
