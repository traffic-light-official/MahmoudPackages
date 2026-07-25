"""Sync/async bridging helpers shared across this package.

The central problem this module solves: DRF's permission classes,
throttle classes, and serializers are synchronous, and often touch the
database (a permission checking group membership, a throttle reading
the cache, a `UniqueValidator` querying for a conflict). Calling that
sync, database-touching code directly from an async view raises
Django's ``SynchronousOnlyOperation`` - it must be run through
``asgiref.sync.sync_to_async`` instead, on a real thread, not just
awaited. Every bridging function in this package uses
``thread_sensitive=True`` (the default), which pins all such calls
within one request to the *same* thread - required for Django's
per-thread database connection handling to stay consistent.
"""

from __future__ import annotations

import asyncio
from typing import Any, TypeVar

from asgiref.sync import sync_to_async

_T = TypeVar("_T")


def is_async_callable(value: Any) -> bool:
    """Return whether ``value`` is a native coroutine function.

    Unlike a bare ``asyncio.iscoroutinefunction`` check, this also sees
    through ``functools.partial`` wrapping, matching how Django's own
    ``iscoroutinefunction`` helper behaves.
    """
    return asyncio.iscoroutinefunction(value)


async def call_maybe_async(func: Any, /, *args: Any, **kwargs: Any) -> Any:
    """Call ``func``, awaiting it directly if async, bridging via a thread if not.

    Args:
        func: A callable - either a native coroutine function, or a
            plain (possibly database-touching) synchronous one.
        *args: Positional arguments to pass to ``func``.
        **kwargs: Keyword arguments to pass to ``func``.

    Returns:
        Whatever ``func`` returns (or resolves to, if a coroutine).
    """
    if is_async_callable(func):
        return await func(*args, **kwargs)
    return await sync_to_async(func, thread_sensitive=True)(*args, **kwargs)
