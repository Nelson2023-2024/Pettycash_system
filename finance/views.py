from typing import Any

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from utils.decorators.allowed_http_methods import allowed_http_methods
from utils.decorators.login_required import login_required

from utils.response_provider import ResponseProvider
from finance.services.expense_request_service import ExpenseRequestController
from .services.pettycash_services import PettyCashService


@csrf_exempt
@allowed_http_methods(["POST"])
@login_required("ADM", "CFO")
def create_petty_cash_view(request) -> ResponseProvider | Any:
    try:
        return PettyCashService.create_petty_cash_account(request)
    except Exception as ex:
        return ResponseProvider.handle_exception(ex)


@csrf_exempt
@allowed_http_methods(["GET"])
@login_required("ADM", "CFO", "FO")
def get_petty_cash_view(request, account_id: str) -> JsonResponse:
    try:
        return PettyCashService.get_petty_cash_account(account_id)
    except Exception as ex:
        return ResponseProvider.handle_exception(ex)


@csrf_exempt
@allowed_http_methods(["GET"])
@login_required("ADM", "CFO", "FO")
def get_all_petty_cash_view(request) -> JsonResponse:
    try:
        return PettyCashService.get_all_petty_cash_accounts()
    except Exception as ex:
        return ResponseProvider.handle_exception(ex)


@csrf_exempt
@allowed_http_methods(["PATCH"])
@login_required("ADM", "CFO")
def update_petty_cash_view(request, account_id: str) -> JsonResponse:
    try:
        return PettyCashService.update_petty_cash_account(request, account_id)
    except Exception as ex:
        return ResponseProvider.handle_exception(ex)


@csrf_exempt
@allowed_http_methods(["DELETE"])
@login_required("ADM", "CFO")
def deactivate_petty_cash_view(request, account_id: str) -> JsonResponse:
    try:
        return PettyCashService.deactivate_petty_cash_account(request, account_id)
    except Exception as ex:
        return ResponseProvider.handle_exception(ex)


# ── EXPENSE REQUESTS ─────────────────────────────────────────
@csrf_exempt
@allowed_http_methods(["POST"])
@login_required("EMP", "FO")  # employees and FO can submit expenses
def create_expense_view(request) -> JsonResponse:
    return ExpenseRequestController().create_expense_request(request)


@csrf_exempt
@allowed_http_methods(["GET"])
@login_required("ADM", "CFO", "FO")
def list_all_expenses_view(request) -> JsonResponse:
    return ExpenseRequestController().get_all_expense_requests(request)


@csrf_exempt
@allowed_http_methods(["GET"])
@login_required("EMP", "FO", "CFO", "ADM")
def list_my_expenses_view(request) -> JsonResponse:
    return ExpenseRequestController().get_auth_user_expense_request(request)


@csrf_exempt
@allowed_http_methods(["PATCH"])
@login_required("EMP", "FO")
def update_expense_view(request, expense_id: str) -> JsonResponse:
    return ExpenseRequestController().update_expense_request(request, expense_id)


@csrf_exempt
@allowed_http_methods(["DELETE"])
@login_required("ADM", "CFO", "EMP")
def deactivate_expense_view(request, expense_request_id: str) -> JsonResponse:
    return ExpenseRequestController().deactivate_auth_expense_request(
        request, expense_request_id
    )
