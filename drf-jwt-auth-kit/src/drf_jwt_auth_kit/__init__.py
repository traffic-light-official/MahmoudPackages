"""Enterprise JWT authentication for Django REST Framework.

The public API is intentionally small. Most projects only need:

* ``"drf_jwt_auth_kit.authentication.JWTAuthentication"`` in
  ``REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]``.
* ``path("auth/", include("drf_jwt_auth_kit.urls"))`` for the
  login/refresh/logout/device/MFA API.

Note:
    This module intentionally does **not** re-export
    :class:`~drf_jwt_auth_kit.authentication.JWTAuthentication`, any
    model, or anything from :mod:`drf_jwt_auth_kit.mfa` (which touches
    the ``TOTPDevice`` model). Django imports every app's top-level
    ``__init__.py`` *before* any app's models are ready (during
    ``AppConfig`` discovery); importing a model-touching module from
    here would raise ``AppRegistryNotReady``. Import those directly from
    their submodule instead, e.g. ``from drf_jwt_auth_kit.models import
    Device`` or ``from drf_jwt_auth_kit.mfa import get_mfa_provider`` -
    see ``docs/quickstart.md`` for a complete end-to-end example.
"""

from __future__ import annotations

from drf_jwt_auth_kit.constants import (
    AUTH_HEADER_PREFIX,
    CLAIM_DEVICE_ID,
    CLAIM_JTI,
    CLAIM_TOKEN_TYPE,
    CLAIM_USER_ID,
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
)
from drf_jwt_auth_kit.csrf import validate_csrf
from drf_jwt_auth_kit.exceptions import (
    AuthKitError,
    DeviceRevokedError,
    InvalidCSRFTokenError,
    InvalidMFACodeError,
    InvalidTokenError,
    MFANotEnrolledError,
    MFARequiredError,
    TokenExpiredError,
    TokenReuseDetectedError,
)
from drf_jwt_auth_kit.settings import app_settings, get_setting
from drf_jwt_auth_kit.tokens import decode_token, encode_access_token, encode_refresh_token

__version__ = "1.0.0"

__all__ = [
    "AUTH_HEADER_PREFIX",
    "CLAIM_DEVICE_ID",
    "CLAIM_JTI",
    "CLAIM_TOKEN_TYPE",
    "CLAIM_USER_ID",
    "TOKEN_TYPE_ACCESS",
    "TOKEN_TYPE_REFRESH",
    "AuthKitError",
    "DeviceRevokedError",
    "InvalidCSRFTokenError",
    "InvalidMFACodeError",
    "InvalidTokenError",
    "MFANotEnrolledError",
    "MFARequiredError",
    "TokenExpiredError",
    "TokenReuseDetectedError",
    "__version__",
    "app_settings",
    "decode_token",
    "encode_access_token",
    "encode_refresh_token",
    "get_setting",
    "validate_csrf",
]
