from typing import Any

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from utils.decorators.allowed_http_methods import allowed_http_methods
from utils.decorators.login_required import login_required

from utils.response_provider import ResponseProvider
from finance.services.expense_request_service import ExpenseRequestController
from finance.services.topup_request_service import TopUpRequestController
from finance.services.disbursment_reconciliation_service import DisbursementReconciliationController
from .services.pettycash_services import PettyCashService


@csrf_exempt
@allowed_http_methods("POST")
@login_required("ADM", "CFO","ADM")
def create_petty_cash_view(request) -> ResponseProvider | Any:
    try:
        return PettyCashService().create_petty_cash_account(request)
    except Exception as ex:
        return ResponseProvider().handle_exception(ex)


@csrf_exempt
@allowed_http_methods("GET")
@login_required("ADM", "CFO", "FO","ADM")
def get_petty_cash_view(request, account_id: str) -> JsonResponse:
    try:
        return PettyCashService().get_petty_cash_account(account_id)
    except Exception as ex:
        return ResponseProvider().handle_exception(ex)


@csrf_exempt
@allowed_http_methods("GET")
@login_required("ADM", "CFO", "FO","ADM")
def get_all_petty_cash_view(request) -> JsonResponse:
    try:
        return PettyCashService().get_all_petty_cash_accounts()
    except Exception as ex:
        return ResponseProvider().handle_exception(ex)


@csrf_exempt
@allowed_http_methods("PATCH")
@login_required("ADM", "CFO","ADM")
def update_petty_cash_view(request, account_id: str) -> JsonResponse:
    try:
        return PettyCashService().update_petty_cash_account(request, account_id)
    except Exception as ex:
        return ResponseProvider().handle_exception(ex)


@csrf_exempt
@allowed_http_methods("DELETE")
@login_required("ADM", "CFO","ADM")
def deactivate_petty_cash_view(request, account_id: str) -> JsonResponse:
    try:
        return PettyCashService().deactivate_petty_cash_account(request, account_id)
    except Exception as ex:
        return ResponseProvider().handle_exception(ex)


# ── EXPENSE REQUESTS ─────────────────────────────────────────
@csrf_exempt
@allowed_http_methods("POST")
@login_required("EMP", "FO","ADM")  # employees and FO can submit expenses
def create_expense_view(request) -> JsonResponse:
    return ExpenseRequestController().create_expense_request(request)


@csrf_exempt
@allowed_http_methods("GET")
@login_required("ADM", "CFO", "FO")
def list_all_expenses_view(request) -> JsonResponse:
    return ExpenseRequestController().get_all_expense_requests(request)


@csrf_exempt
@allowed_http_methods("GET")
@login_required("EMP", "FO", "CFO", "ADM")
def list_my_expenses_view(request) -> JsonResponse:
    return ExpenseRequestController().get_auth_user_expense_request(request)


@csrf_exempt
@allowed_http_methods("PATCH")
@login_required("EMP", "FO","ADM")
def update_expense_view(request, expense_id: str) -> JsonResponse:
    return ExpenseRequestController().update_expense_request(request, expense_id)


@csrf_exempt
@allowed_http_methods("DELETE")
@login_required("ADM", "CFO", "EMP")
def deactivate_expense_view(request, expense_request_id: str) -> JsonResponse:
    return ExpenseRequestController().deactivate_auth_expense_request(
        request, expense_request_id
    )

@csrf_exempt
@allowed_http_methods("PATCH")
@login_required("FO", "CFO", "ADM")
def decide_expense_view(request, expense_id: str) -> JsonResponse:
    return ExpenseRequestController().approve_or_rejext_expense_request(request, expense_id)


@csrf_exempt
@allowed_http_methods("POST")
@login_required("FO", "CFO", "ADM")
def disburse_expense_view(request, expense_id: str) -> JsonResponse:
    return ExpenseRequestController().disburse_expense_request(request, expense_id)

# ── TOP UP REQUESTS ──────────────────────────────────────────
@csrf_exempt
@allowed_http_methods("POST")
@login_required("FO","ADM")  # only Finance Officer can request top-ups
def create_topup_view(request, pettycash_account_id: str) -> JsonResponse:
    return TopUpRequestController().create(request, pettycash_account_id)


@csrf_exempt
@allowed_http_methods("GET")
@login_required("ADM", "CFO", "FO")
def list_all_topups_view(request) -> JsonResponse:
    return TopUpRequestController().list_all(request)


@csrf_exempt
@allowed_http_methods("GET")
@login_required("ADM", "CFO", "FO")
def list_my_topups_view(request) -> JsonResponse:
    return TopUpRequestController().list_auth_user_requests(request)


@csrf_exempt
@allowed_http_methods("PATCH")
@login_required("CFO","ADM")  # only CFO can approve/reject
def decide_topup_view(request, topup_id: str) -> JsonResponse:
    return TopUpRequestController().decide(request, topup_id)


@csrf_exempt
@allowed_http_methods("POST")
@login_required("CFO","ADM")  # Finance Officer disburses after CFO approves
def disburse_topup_view(request, topup_id: str) -> JsonResponse:
    return TopUpRequestController().disburse(request, topup_id)


@csrf_exempt
@allowed_http_methods("PATCH")
@login_required("FO","ADM")  # only requester role can edit their own pending request
def update_topup_view(request, topup_id: str) -> JsonResponse:
    return TopUpRequestController().update(request, topup_id)


@csrf_exempt
@allowed_http_methods("DELETE")
@login_required("ADM", "CFO", "FO")
def deactivate_topup_view(request, topup_id: str) -> JsonResponse:
    return TopUpRequestController().deactivate(request, topup_id)


# ── DISBURSEMENT RECONCILIATION ──────────────────────────────
@csrf_exempt
@allowed_http_methods("GET")
@login_required("EMP", "FO", "ADM")
def list_my_reconciliations_view(request) -> JsonResponse:
    return DisbursementReconciliationController().get_my_reconciliations(request)


@csrf_exempt
@allowed_http_methods("GET")
@login_required("ADM", "CFO", "FO")
def list_all_reconciliations_view(request) -> JsonResponse:
    return DisbursementReconciliationController().get_all_reconciliations(request)


@csrf_exempt
@allowed_http_methods("GET")
@login_required("EMP", "FO", "CFO", "ADM")
def get_reconciliation_view(request, reconciliation_id: str) -> JsonResponse:
    return DisbursementReconciliationController().get_reconciliation(request, reconciliation_id)


@csrf_exempt
@allowed_http_methods("POST")
@login_required("EMP", "ADM")  # only the employee submits their own receipt
def submit_reconciliation_receipt_view(request, reconciliation_id: str) -> JsonResponse:
    return DisbursementReconciliationController().submit_reconciliation_receipt(request, reconciliation_id)


@csrf_exempt
@allowed_http_methods("PATCH")
@login_required("FO", "CFO", "ADM")  # only FO/CFO can review
def review_reconciliation_view(request, reconciliation_id: str) -> JsonResponse:
    return DisbursementReconciliationController().review_reconciliation(request, reconciliation_id)