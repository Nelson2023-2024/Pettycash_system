from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from audit.services.dashboard_service import DashBoardController
from utils.decorators.allowed_http_methods import allowed_http_methods
from utils.decorators.login_required import login_required
from audit.services.notification_service import NotificationController


# ── NOTIFICATIONS ────────────────────────────────────────────
@csrf_exempt
@allowed_http_methods("GET")
@login_required("EMP", "FO", "CFO", "ADM")
def list_my_notifications_view(request) -> JsonResponse:
    return NotificationController().get_my_notifications(request)


@csrf_exempt
@allowed_http_methods("GET")
@login_required("EMP", "FO", "CFO", "ADM")
def get_unread_count_view(request) -> JsonResponse:
    return NotificationController().get_unread_count(request)


@csrf_exempt
@allowed_http_methods("PATCH")
@login_required("EMP", "FO", "CFO", "ADM")
def mark_notification_as_read_view(request, notification_id: str) -> JsonResponse:
    return NotificationController().mark_notification_as_read(request, notification_id)


@csrf_exempt
@allowed_http_methods("PATCH")
@login_required("EMP", "FO", "CFO", "ADM")
def mark_all_notifications_as_read_view(request) -> JsonResponse:
    return NotificationController().mark_all_notifications_as_read(request)


# ── DASHBOARD ────────────────────────────────────────────
def employee_dashboard_view(request):
    return DashBoardController().get_employee_dashboard(request)


@csrf_exempt
@allowed_http_methods("GET")
@login_required("EMP", "FO", "CFO", "ADM")
def dashboard_view(request):
    return DashBoardController().get_dashboard(request)
