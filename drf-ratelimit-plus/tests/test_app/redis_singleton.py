"""A dotted-path-resolvable Redis client/factory, for testing REDIS_CLIENT."""

from __future__ import annotations

import fakeredis

CLIENT = fakeredis.FakeRedis()


def build_client() -> fakeredis.FakeRedis:
    return fakeredis.FakeRedis()
