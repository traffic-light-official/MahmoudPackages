"""DRF views: login, refresh, logout, devices, login history, and TOTP enrollment."""

from __future__ import annotations

from typing import Any

from django.contrib.auth import authenticate, get_user_model
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_jwt_auth_kit.constants import (
    CLAIM_DEVICE_ID,
    LOGIN_FAILURE_INVALID_CREDENTIALS,
    LOGIN_FAILURE_INVALID_MFA_CODE,
    LOGIN_FAILURE_MFA_REQUIRED,
    REVOKED_REASON_LOGOUT,
    REVOKED_REASON_LOGOUT_ALL,
    TOKEN_TYPE_REFRESH,
)
from drf_jwt_auth_kit.cookies import (
    clear_csrf_cookie,
    clear_refresh_cookie,
    set_csrf_cookie,
    set_refresh_cookie,
)
from drf_jwt_auth_kit.csrf import validate_csrf
from drf_jwt_auth_kit.devices import create_device, revoke_all_devices, revoke_device
from drf_jwt_auth_kit.exceptions import (
    DeviceRevokedError,
    InvalidCSRFTokenError,
    InvalidTokenError,
    TokenExpiredError,
    TokenReuseDetectedError,
)
from drf_jwt_auth_kit.mfa import (
    generate_totp_secret,
    get_mfa_provider,
    totp_provisioning_uri,
    verify_totp_code,
)
from drf_jwt_auth_kit.models import Device, LoginHistory, TOTPDevice
from drf_jwt_auth_kit.rotation import issue_token_pair, rotate_refresh_token
from drf_jwt_auth_kit.serializers import (
    DeviceSerializer,
    LoginHistorySerializer,
    LoginSerializer,
    TOTPConfirmSerializer,
    TOTPSetupResponseSerializer,
)
from drf_jwt_auth_kit.settings import get_setting
from drf_jwt_auth_kit.tokens import decode_token


def _client_ip(request: HttpRequest) -> str | None:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return str(forwarded_for.split(",")[0].strip())
    remote_addr = request.META.get("REMOTE_ADDR")
    return remote_addr if remote_addr else None


def _record_login_history(
    *,
    request: HttpRequest,
    username: str,
    user: Any,
    device: Device | None,
    success: bool,
    failure_reason: str = "",
) -> None:
    if not get_setting("LOGIN_HISTORY_ENABLED"):
        return
    LoginHistory.objects.create(
        user=user,
        username_attempted=username,
        device=device,
        ip_address=_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
        success=success,
        failure_reason=failure_reason,
    )


class LoginView(APIView):
    """Authenticates a user, optionally enforcing MFA, and issues a token pair."""

    permission_classes = [permissions.AllowAny]
    authentication_classes: list[Any] = []

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = authenticate(request, username=data["username"], password=data["password"])
        if user is None:
            _record_login_history(
                request=request,
                username=data["username"],
                user=None,
                device=None,
                success=False,
                failure_reason=LOGIN_FAILURE_INVALID_CREDENTIALS,
            )
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        mfa_provider = get_mfa_provider()
        if mfa_provider.is_required(user):
            if not data["mfa_code"]:
                _record_login_history(
                    request=request,
                    username=data["username"],
                    user=user,
                    device=None,
                    success=False,
                    failure_reason=LOGIN_FAILURE_MFA_REQUIRED,
                )
                return Response({"mfa_required": True}, status=status.HTTP_401_UNAUTHORIZED)
            if not mfa_provider.verify(user, data["mfa_code"]):
                _record_login_history(
                    request=request,
                    username=data["username"],
                    user=user,
                    device=None,
                    success=False,
                    failure_reason=LOGIN_FAILURE_INVALID_MFA_CODE,
                )
                return Response(
                    {"mfa_required": True, "detail": "Invalid MFA code."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        device = create_device(user=user, request=request, label=data["device_label"])
        pair = issue_token_pair(user=user, device=device, remember_me=data["remember_me"])
        _record_login_history(
            request=request, username=data["username"], user=user, device=device, success=True
        )

        response = Response(
            {
                "access_token": pair.access_token,
                "device": DeviceSerializer(device, context={"current_device_id": device.pk}).data,
            },
            status=status.HTTP_200_OK,
        )
        set_refresh_cookie(response, pair.refresh_token)
        set_csrf_cookie(response)
        return response


class RefreshView(APIView):
    """Rotates the refresh token found in the httpOnly cookie and issues a new access token."""

    permission_classes = [permissions.AllowAny]
    authentication_classes: list[Any] = []

    def post(self, request: Request) -> Response:
        try:
            validate_csrf(request)
        except InvalidCSRFTokenError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        raw_refresh_token = request.COOKIES.get(get_setting("REFRESH_COOKIE_NAME"))
        if not raw_refresh_token:
            return Response(
                {"detail": "No refresh token cookie present."}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            pair = rotate_refresh_token(raw_refresh_token)
        except TokenExpiredError as exc:
            return self._unauthenticated_and_clear(str(exc))
        except (InvalidTokenError, DeviceRevokedError, TokenReuseDetectedError) as exc:
            return self._unauthenticated_and_clear(str(exc))

        response = Response({"access_token": pair.access_token}, status=status.HTTP_200_OK)
        set_refresh_cookie(response, pair.refresh_token)
        set_csrf_cookie(response)
        return response

    def _unauthenticated_and_clear(self, detail: str) -> Response:
        response = Response({"detail": detail}, status=status.HTTP_401_UNAUTHORIZED)
        clear_refresh_cookie(response)
        clear_csrf_cookie(response)
        return response


class LogoutView(APIView):
    """Revokes the current device (identified by the refresh cookie) and clears cookies."""

    permission_classes = [permissions.AllowAny]
    authentication_classes: list[Any] = []

    def post(self, request: Request) -> Response:
        try:
            validate_csrf(request)
        except InvalidCSRFTokenError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        raw_refresh_token = request.COOKIES.get(get_setting("REFRESH_COOKIE_NAME"))
        if raw_refresh_token:
            try:
                claims = decode_token(raw_refresh_token, expected_type=TOKEN_TYPE_REFRESH)
                device = Device.objects.get(pk=claims[CLAIM_DEVICE_ID])
            except (InvalidTokenError, TokenExpiredError, Device.DoesNotExist):
                device = None
            if device is not None:
                revoke_device(device, reason=REVOKED_REASON_LOGOUT)

        response = Response({"detail": "Logged out."}, status=status.HTTP_200_OK)
        clear_refresh_cookie(response)
        clear_csrf_cookie(response)
        return response


class LogoutAllView(APIView):
    """Revokes every device belonging to the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        # IsAuthenticated guarantees request.user is a real user, never AnonymousUser.
        revoked = revoke_all_devices(request.user, reason=REVOKED_REASON_LOGOUT_ALL)  # type: ignore[arg-type]
        response = Response({"revoked_devices": revoked}, status=status.HTTP_200_OK)
        clear_refresh_cookie(response)
        clear_csrf_cookie(response)
        return response


class DeviceViewSet(
    mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet[Device]
):
    """Lists the authenticated user's own active devices and lets them revoke one."""

    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Device]:
        return Device.objects.filter(user=self.request.user, revoked_at__isnull=True)  # type: ignore[misc]

    def get_serializer_context(self) -> dict[str, Any]:
        context: dict[str, Any] = dict(super().get_serializer_context())
        auth = getattr(self.request, "auth", None)
        context["current_device_id"] = auth.get(CLAIM_DEVICE_ID) if isinstance(auth, dict) else None
        return context

    def perform_destroy(self, instance: Device) -> None:
        revoke_device(instance, reason=REVOKED_REASON_LOGOUT)


class LoginHistoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet[LoginHistory]):
    """Lists the authenticated user's own login history."""

    serializer_class = LoginHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[LoginHistory]:
        return LoginHistory.objects.filter(user=self.request.user)  # type: ignore[misc]


class TOTPSetupView(APIView):
    """Begins TOTP enrollment: generates a secret and a provisioning URI for a QR code."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        existing = TOTPDevice.objects.filter(user=request.user).first()  # type: ignore[misc]
        if existing is not None and existing.confirmed:
            return Response(
                {"detail": "TOTP is already enabled."}, status=status.HTTP_400_BAD_REQUEST
            )

        secret = generate_totp_secret()
        TOTPDevice.objects.update_or_create(  # type: ignore[misc]
            user=request.user, defaults={"secret": secret, "confirmed": False}
        )
        username_field = get_user_model().USERNAME_FIELD
        account_name = str(getattr(request.user, username_field))
        uri = totp_provisioning_uri(secret=secret, account_name=account_name)
        return Response(
            TOTPSetupResponseSerializer({"secret": secret, "provisioning_uri": uri}).data
        )


class TOTPConfirmView(APIView):
    """Confirms TOTP enrollment by verifying the first generated code."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = TOTPConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            totp_device = TOTPDevice.objects.get(user=request.user)  # type: ignore[misc]
        except TOTPDevice.DoesNotExist:
            return Response(
                {"detail": "TOTP setup has not been started."}, status=status.HTTP_400_BAD_REQUEST
            )

        if not verify_totp_code(totp_device.secret, serializer.validated_data["code"]):
            return Response({"detail": "Invalid code."}, status=status.HTTP_400_BAD_REQUEST)

        totp_device.confirmed = True
        totp_device.confirmed_at = timezone.now()
        totp_device.save(update_fields=["confirmed", "confirmed_at"])
        return Response({"detail": "MFA enabled."})


class TOTPDisableView(APIView):
    """Disables TOTP for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        deleted, _details = TOTPDevice.objects.filter(user=request.user).delete()  # type: ignore[misc]
        if not deleted:
            return Response({"detail": "MFA was not enabled."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "MFA disabled."})
