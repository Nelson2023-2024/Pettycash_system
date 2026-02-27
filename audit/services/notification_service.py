from services.services import NotificationService
from utils.response_provider import ResponseProvider

class NotificationController:

    @classmethod
    def get_my_notifications(cls, request):
        """
        Retrieves all notifications for the authenticated user ordered by
        most recent first, with full transaction log context pre-fetched.

        Args:
            request: The HTTP request object.

        Returns:
            JsonResponse: 200 with list of serialized notifications.
        """
        try:
            notifications = NotificationService().list_auth_user_notifications(
                auth_user=request.user.id
            )
            return ResponseProvider.success(
                data=[cls._serialize(n) for n in notifications]
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @classmethod
    def get_unread_count(cls, request):
        """
        Returns the count of unread notifications for the authenticated user.
        Used for the notification badge/counter in the UI.

        Args:
            request: The HTTP request object.

        Returns:
            JsonResponse: 200 with unread count.
        """
        try:
            count = NotificationService().get_unread_count(auth_user=request.user.id)
            return ResponseProvider.success(data={"unread_count": count})
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @classmethod
    def mark_notification_as_read(cls, request, notification_id: str):
        """
        Marks a single notification as read for the authenticated user.
        Scoped to the authenticated user — cannot mark another user's notification.

        Args:
            request: The HTTP request object.
            notification_id (str): The UUID of the notification to mark as read.

        Returns:
            JsonResponse: 200 with serialized updated notification on success.
        """
        try:
            notification = NotificationService().mark_as_read(
                notification_id=notification_id,
                auth_user=request.user,
            )
            return ResponseProvider.success(
                message="Notification marked as read.",
                data=cls._serialize(notification),
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @classmethod
    def mark_all_notifications_as_read(cls, request):
        """
        Marks all unread notifications as read for the authenticated user.

        Args:
            request: The HTTP request object.

        Returns:
            JsonResponse: 200 with count of notifications updated.
        """
        try:
            updated_count = NotificationService().get_mark_all_as_read(
                auth_user=request.user
            )
            return ResponseProvider.success(
                message="All notifications marked as read.",
                data={"updated_count": updated_count},
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @staticmethod
    def _serialize(notification) -> dict:
        """
        Converting a Notifications model → JSON-safe dictionary.
        Resolves all pre-fetched related fields — no extra DB hits if
        select_related was applied in the service query.
        """
        log = notification.transaction_log
        return {
            "id": str(notification.id),
            "channel": notification.channel,
            "is_read": notification.is_read,
            "read_at": notification.read_at.isoformat() if notification.read_at else None,
            "created_at": notification.created_at.isoformat(),
            # transaction log fields
            "message": log.event_message,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            # sender — who triggered the event
            "sender": log.triggered_by.email if log.triggered_by else "System",
            # event fields
            "event_code": log.event_type.code,
            "event_name": log.event_type.name,
            "event_category": log.event_type.event_category.name,
            # log status
            "log_status": log.status.name,
        }