# Advanced Usage

## MFA with TOTP

Enable the built-in provider:

```python
JWT_AUTH_KIT = {"MFA_PROVIDER": "drf_jwt_auth_kit.mfa.TOTPProvider"}
```

MFA is per-user opt-in: a user must complete enrollment (`POST
/auth/mfa/totp/setup/` then `/confirm/`) before
`TOTPProvider.is_required()` returns `True` for them - see
[Quick Start](quickstart.md#enrolling-in-mfa).

## Custom MFA providers

Implement `MFAProvider` for SMS OTP, WebAuthn, backup codes, or
anything else:

```python
from drf_jwt_auth_kit.mfa import MFAProvider


class SmsOtpProvider(MFAProvider):
    def is_required(self, user):
        return getattr(user, "phone_verified", False)

    def verify(self, user, code):
        return sms_otp_service.check(user.phone_number, code)
```

```python
JWT_AUTH_KIT = {"MFA_PROVIDER": "myproject.mfa.SmsOtpProvider"}
```

## Custom exception mapping for reuse detection

`rotate_refresh_token()` raises
`~drf_jwt_auth_kit.exceptions.TokenReuseDetectedError` when a
stolen/replayed refresh token is detected. Log it distinctly from a
plain expired/invalid token - it is a security-relevant event, not just
a client bug:

```python
from drf_jwt_auth_kit.exceptions import TokenReuseDetectedError
from drf_jwt_auth_kit.rotation import rotate_refresh_token

try:
    pair = rotate_refresh_token(raw_refresh_token)
except TokenReuseDetectedError:
    logger.warning("Refresh token reuse detected", extra={"user_id": ...})
    raise
```

(The shipped `RefreshView` already does the equivalent - revoking the
device and returning 401 - this is only needed if you build your own
refresh endpoint on top of `drf_jwt_auth_kit.rotation` directly.)

## Asymmetric signing (RS256)

```python
JWT_AUTH_KIT = {
    "ALGORITHM": "RS256",
    "SIGNING_KEY": open("private_key.pem").read(),
    "VERIFYING_KEY": open("public_key.pem").read(),
}
```

Useful when a separate service needs to verify access tokens without
holding the ability to mint new ones - distribute only the public key.

## Building your own login view

Most projects use `LoginView` as-is, but the building blocks are public
if you need custom logic (e.g. a social-login callback that still needs
to issue this package's tokens):

```python
from drf_jwt_auth_kit.devices import create_device
from drf_jwt_auth_kit.rotation import issue_token_pair
from drf_jwt_auth_kit.cookies import set_csrf_cookie, set_refresh_cookie


def social_login_callback(request, user):
    device = create_device(user=user, request=request, label="Google Sign-In")
    pair = issue_token_pair(user=user, device=device)

    response = Response({"access_token": pair.access_token})
    set_refresh_cookie(response, pair.refresh_token)
    set_csrf_cookie(response)
    return response
```

## Tuning reuse detection

`BLACKLIST_AFTER_ROTATION = False` disables reuse detection entirely
(multiple valid refresh tokens can coexist for a device). This is not
recommended, but exists for projects with unusual client architectures
(e.g. multiple tabs that each independently hold a stale in-memory copy
of a refresh token and cannot coordinate rotation). Prefer fixing the
client to always read the latest cookie instead of reaching for this.

## Cleaning up old tokens

```bash
python manage.py cleanup_expired_tokens
```

Deletes `RefreshToken` rows that expired more than a day ago. Safe to
run on a schedule - see [Deployment](deployment.md).
