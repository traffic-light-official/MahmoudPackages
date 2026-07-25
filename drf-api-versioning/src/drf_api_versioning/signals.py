"""Signals sent by :mod:`drf_api_versioning`.

Connect to these for your own observability (metrics, structured
logging, a usage-tracking model) - this package does not persist
anything itself.
"""

from __future__ import annotations

from django.dispatch import Signal

#: Sent once per request that resolves to a deprecated (but not yet
#: rejected) API version.
#:
#: Providing arguments:
#:     request: The DRF ``Request`` being processed.
#:     version (str): The resolved version name.
#:     version_info (~drf_api_versioning.registry.VersionInfo): Its metadata.
deprecated_version_used = Signal()
