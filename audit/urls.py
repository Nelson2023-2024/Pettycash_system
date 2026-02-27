from django.urls import path
from .views import (
    list_my_notifications_view,
    get_unread_count_view,
    mark_notification_as_read_view,
    mark_all_notifications_as_read_view, dashboard_view,
)

urlpatterns = [
    # ── notifications ────────────────────────────────────────
    path('notifications/', list_my_notifications_view, name='list-my-notifications'),
    path('notifications/unread/count/', get_unread_count_view, name='get-unread-count'),
    path('notifications/<str:notification_id>/read/', mark_notification_as_read_view, name='mark-notification-as-read'),
    path('notifications/read/all/', mark_all_notifications_as_read_view, name='mark-all-notifications-as-read'),

    # ── notifications ────────────────────────────────────────
    path('dashboard/', dashboard_view, name='dashboard')
]