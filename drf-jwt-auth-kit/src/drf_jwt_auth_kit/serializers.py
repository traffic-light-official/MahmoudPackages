"""DRF serializers for login, MFA enrollment, and the device/session API."""

from __future__ import annotations

from rest_framework import serializers

from drf_jwt_auth_kit.models import Device, LoginHistory


class LoginSerializer(serializers.Serializer[dict[str, object]]):
    """Validates a login request's credentials and optional MFA code."""

    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False, style={"input_type": "password"})
    mfa_code = serializers.CharField(required=False, allow_blank=True, default="")
    remember_me = serializers.BooleanField(required=False, default=False)
    device_label = serializers.CharField(required=False, allow_blank=True, default="")


class DeviceSerializer(serializers.ModelSerializer[Device]):
    """Read-only representation of one logged-in device/session."""

    is_current = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = ["id", "label", "user_agent", "created_at", "last_used_at", "is_current"]
        read_only_fields = fields

    def get_is_current(self, device: Device) -> bool:
        current_device_id = self.context.get("current_device_id")
        return current_device_id is not None and str(device.pk) == str(current_device_id)


class LoginHistorySerializer(serializers.ModelSerializer[LoginHistory]):
    """Read-only representation of one login attempt."""

    class Meta:
        model = LoginHistory
        fields = [
            "id",
            "username_attempted",
            "ip_address",
            "user_agent",
            "success",
            "failure_reason",
            "created_at",
        ]
        read_only_fields = fields


class TOTPSetupResponseSerializer(serializers.Serializer[dict[str, str]]):
    """The secret and QR-code provisioning URI returned when starting TOTP enrollment."""

    secret = serializers.CharField(read_only=True)
    provisioning_uri = serializers.CharField(read_only=True)


class TOTPConfirmSerializer(serializers.Serializer[dict[str, str]]):
    """Validates the code supplied to confirm TOTP enrollment."""

    code = serializers.CharField()
