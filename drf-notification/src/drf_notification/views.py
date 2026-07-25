"""DRF views for the notification preference center."""

from __future__ import annotations

from typing import Any

from django.db.models import QuerySet
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from drf_notification.constants import ALL_CHANNELS
from drf_notification.exceptions import InvalidUnsubscribeTokenError
from drf_notification.models import (
    Notification,
    NotificationPreference,
    NotificationSettings,
    WebhookTarget,
)
from drf_notification.serializers import (
    NotificationPreferenceSerializer,
    NotificationSerializer,
    NotificationSettingsSerializer,
    WebhookTargetSerializer,
)
from drf_notification.unsubscribe import resolve_unsubscribe_token


class NotificationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet[Notification]
):
    """Lists the authenticated user's own notifications and lets them mark one read."""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Notification]:
        # self.request.user is `User | AnonymousUser` per DRF's Request typing;
        # IsAuthenticated guarantees a real user reaches this point at runtime.
        return Notification.objects.filter(recipient=self.request.user)  # type: ignore[misc]

    @action(detail=True, methods=["post"])
    def mark_read(self, request: Request, pk: str | None = None) -> Response:
        notification = self.get_object()
        notification.mark_read()
        return Response(self.get_serializer(notification).data)

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request: Request) -> Response:
        updated = self.get_queryset().filter(read_at__isnull=True).update(read_at=timezone.now())
        return Response({"marked_read": updated})


class NotificationPreferenceViewSet(viewsets.ModelViewSet[NotificationPreference]):
    """CRUD for the authenticated user's own per-event-type/channel preferences."""

    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[NotificationPreference]:
        return NotificationPreference.objects.filter(user=self.request.user)  # type: ignore[misc]

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        serializer.save(user=self.request.user)


class WebhookTargetViewSet(viewsets.ModelViewSet[WebhookTarget]):
    """CRUD for the authenticated user's own webhook targets."""

    serializer_class = WebhookTargetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[WebhookTarget]:
        return WebhookTarget.objects.filter(user=self.request.user)  # type: ignore[misc]

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        serializer.save(user=self.request.user)


class NotificationSettingsView(APIView):
    """Retrieve/update the authenticated user's notification settings (one row per user)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        # request.user is `User | AnonymousUser` per DRF's Request typing;
        # IsAuthenticated guarantees a real user reaches this point at runtime.
        settings_obj, _ = NotificationSettings.objects.get_or_create(  # type: ignore[misc]
            user=request.user
        )
        return Response(NotificationSettingsSerializer(settings_obj).data)

    def patch(self, request: Request) -> Response:
        settings_obj, _ = NotificationSettings.objects.get_or_create(  # type: ignore[misc]
            user=request.user
        )
        serializer = NotificationSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UnsubscribeView(APIView):
    """Public, signed-token unsubscribe endpoint - no authentication required."""

    permission_classes = [permissions.AllowAny]
    authentication_classes: list[Any] = []

    def post(self, request: Request, token: str) -> Response:
        try:
            user_id, event_key = resolve_unsubscribe_token(token)
        except InvalidUnsubscribeTokenError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if event_key is None:
            settings_obj, _ = NotificationSettings.objects.get_or_create(user_id=user_id)
            settings_obj.unsubscribed_all = True
            settings_obj.save(update_fields=["unsubscribed_all"])
        else:
            for channel in ALL_CHANNELS:
                NotificationPreference.objects.update_or_create(
                    user_id=user_id,
                    event_key=event_key,
                    channel=channel,
                    defaults={"enabled": False},
                )
        return Response({"detail": "Unsubscribed."})


class PreferenceCenterView(APIView):
    """Public, stable-token read-only snapshot of a user's notification settings.

    Intended for a "manage my notifications" page built against a
    long-lived link (unlike :class:`UnsubscribeView`'s expiring, one-shot
    token) - see
    :attr:`~drf_notification.models.NotificationSettings.unsubscribe_token`.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes: list[Any] = []

    def get(self, request: Request, token: str) -> Response:
        try:
            settings_obj = NotificationSettings.objects.get(unsubscribe_token=token)
        except NotificationSettings.DoesNotExist:
            return Response({"detail": "Invalid token."}, status=status.HTTP_404_NOT_FOUND)

        preferences = NotificationPreference.objects.filter(user_id=settings_obj.user_id)
        return Response(
            {
                "settings": NotificationSettingsSerializer(settings_obj).data,
                "preferences": NotificationPreferenceSerializer(preferences, many=True).data,
            }
        )
