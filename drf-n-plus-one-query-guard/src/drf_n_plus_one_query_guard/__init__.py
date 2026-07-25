"""Detect N+1 query patterns in Django REST Framework views.

The public API is intentionally small. Most projects only need one of:

* :class:`~drf_n_plus_one_query_guard.testing.assert_no_n_plus_one` - a
  test-time context manager, independent of any Django setting.
* :class:`~drf_n_plus_one_query_guard.middleware.NPlusOneGuardMiddleware` -
  guard every request in development/staging.
* :func:`~drf_n_plus_one_query_guard.decorators.guard_view` - guard one
  specific view/action.

but the underlying pieces (:class:`~drf_n_plus_one_query_guard.guard.NPlusOneGuard`,
:class:`~drf_n_plus_one_query_guard.tracker.QueryTracker`) are all
importable directly for custom integrations.
"""

from __future__ import annotations

from drf_n_plus_one_query_guard.decorators import guard_view
from drf_n_plus_one_query_guard.exceptions import NPlusOneDetectedError, NPlusOneGuardError
from drf_n_plus_one_query_guard.fingerprint import normalize_sql
from drf_n_plus_one_query_guard.guard import NPlusOneGuard
from drf_n_plus_one_query_guard.middleware import NPlusOneGuardMiddleware
from drf_n_plus_one_query_guard.testing import assert_no_n_plus_one
from drf_n_plus_one_query_guard.tracker import QueryEvent, QueryTracker, Violation

__version__ = "1.0.0"

__all__ = [
    "NPlusOneDetectedError",
    "NPlusOneGuard",
    "NPlusOneGuardError",
    "NPlusOneGuardMiddleware",
    "QueryEvent",
    "QueryTracker",
    "Violation",
    "__version__",
    "assert_no_n_plus_one",
    "guard_view",
    "normalize_sql",
]
