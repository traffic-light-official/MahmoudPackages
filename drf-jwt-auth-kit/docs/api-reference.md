# API Reference

This page documents every public class, function, and exception. It is
generated in part from the source docstrings via
[mkdocstrings](https://mkdocstrings.github.io/) - the same text you'll see
in your editor's tooltips.

## Authentication

### JWTAuthentication

::: drf_jwt_auth_kit.authentication.JWTAuthentication

## Tokens

### encode_access_token

::: drf_jwt_auth_kit.tokens.encode_access_token

### encode_refresh_token

::: drf_jwt_auth_kit.tokens.encode_refresh_token

### decode_token

::: drf_jwt_auth_kit.tokens.decode_token

### token_type_of

::: drf_jwt_auth_kit.tokens.token_type_of

## Rotation

### issue_token_pair

::: drf_jwt_auth_kit.rotation.issue_token_pair

### rotate_refresh_token

::: drf_jwt_auth_kit.rotation.rotate_refresh_token

### TokenPair

::: drf_jwt_auth_kit.rotation.TokenPair

## Devices

### create_device

::: drf_jwt_auth_kit.devices.create_device

### touch_device

::: drf_jwt_auth_kit.devices.touch_device

### revoke_device

::: drf_jwt_auth_kit.devices.revoke_device

### revoke_all_devices

::: drf_jwt_auth_kit.devices.revoke_all_devices

## Models

### Device

::: drf_jwt_auth_kit.models.Device

### RefreshToken

::: drf_jwt_auth_kit.models.RefreshToken

### LoginHistory

::: drf_jwt_auth_kit.models.LoginHistory

### TOTPDevice

::: drf_jwt_auth_kit.models.TOTPDevice

## Cookies

### set_refresh_cookie

::: drf_jwt_auth_kit.cookies.set_refresh_cookie

### clear_refresh_cookie

::: drf_jwt_auth_kit.cookies.clear_refresh_cookie

### set_csrf_cookie

::: drf_jwt_auth_kit.cookies.set_csrf_cookie

### clear_csrf_cookie

::: drf_jwt_auth_kit.cookies.clear_csrf_cookie

## CSRF

### validate_csrf

::: drf_jwt_auth_kit.csrf.validate_csrf

## MFA

### MFAProvider

::: drf_jwt_auth_kit.mfa.MFAProvider

### NullMFAProvider

::: drf_jwt_auth_kit.mfa.NullMFAProvider

### TOTPProvider

::: drf_jwt_auth_kit.mfa.TOTPProvider

### generate_totp_secret

::: drf_jwt_auth_kit.mfa.generate_totp_secret

### totp_provisioning_uri

::: drf_jwt_auth_kit.mfa.totp_provisioning_uri

### verify_totp_code

::: drf_jwt_auth_kit.mfa.verify_totp_code

### get_mfa_provider

::: drf_jwt_auth_kit.mfa.get_mfa_provider

## DRF views

### LoginView

::: drf_jwt_auth_kit.views.LoginView

### RefreshView

::: drf_jwt_auth_kit.views.RefreshView

### LogoutView

::: drf_jwt_auth_kit.views.LogoutView

### LogoutAllView

::: drf_jwt_auth_kit.views.LogoutAllView

### DeviceViewSet

::: drf_jwt_auth_kit.views.DeviceViewSet

### LoginHistoryViewSet

::: drf_jwt_auth_kit.views.LoginHistoryViewSet

### TOTPSetupView

::: drf_jwt_auth_kit.views.TOTPSetupView

### TOTPConfirmView

::: drf_jwt_auth_kit.views.TOTPConfirmView

### TOTPDisableView

::: drf_jwt_auth_kit.views.TOTPDisableView

## Exceptions

### AuthKitError

::: drf_jwt_auth_kit.exceptions.AuthKitError

### InvalidTokenError

::: drf_jwt_auth_kit.exceptions.InvalidTokenError

### TokenExpiredError

::: drf_jwt_auth_kit.exceptions.TokenExpiredError

### TokenReuseDetectedError

::: drf_jwt_auth_kit.exceptions.TokenReuseDetectedError

### DeviceRevokedError

::: drf_jwt_auth_kit.exceptions.DeviceRevokedError

### InvalidCSRFTokenError

::: drf_jwt_auth_kit.exceptions.InvalidCSRFTokenError

### MFARequiredError

::: drf_jwt_auth_kit.exceptions.MFARequiredError

### InvalidMFACodeError

::: drf_jwt_auth_kit.exceptions.InvalidMFACodeError

### MFANotEnrolledError

::: drf_jwt_auth_kit.exceptions.MFANotEnrolledError

## Settings

### get_setting

::: drf_jwt_auth_kit.settings.get_setting

### get_signing_key

::: drf_jwt_auth_kit.settings.get_signing_key

### get_verifying_key

::: drf_jwt_auth_kit.settings.get_verifying_key
