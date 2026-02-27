from django.db.models.functions import TruncMonth, TruncDay

from utils.response_provider import ResponseProvider
from django.db.models import Count, Sum, F
from datetime import timedelta
from django.utils import timezone
from services.services import (
    ExpenseRequestService,
    PettyCashAccountService,
    TopUpRequestService,
    DisbursementReconciliationService,
    TransactionLogService,
)


class DashBoardController:

    @classmethod
    def get_dashboard(cls, request):
        """
        Single comprehensive dashboard endpoint.
        Returns all dashboard data in one response.
        Frontend is responsible for rendering only what
        is relevant to the authenticated user's role.

        Returns:
            JsonResponse: 200 with full dashboard data.
        """
        try:
            today = timezone.now()
            month_start = today.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )  # Changes today's date to the first day of this month at 00:00
            last_6_months = today - timedelta(days=180)
            auth_user = request.user

            expenses = ExpenseRequestService().filter(is_active=True)
            my_expenses = ExpenseRequestService().filter(
                is_active=True, employee=auth_user
            )
            my_reconciliations = DisbursementReconciliationService().filter(
                submitted_by=auth_user
            )
            petty_cash_accounts = PettyCashAccountService().filter(is_active=True)

            # approval rate
            approved_count = (
                TransactionLogService()
                .filter(
                    event_type__code="expense_approved",  # Find TransactionLogs where the related EventType has code = expense_approved
                    created_at__gte=month_start,  # Only logs created from the first day of this month until now
                )
                .count()
            )

            rejected_count = (
                TransactionLogService()
                .filter(
                    event_type__code="expense_rejected", created_at__gte=month_start
                )
                .count()
            )

            total_decisions = approved_count + rejected_count
            approval_rate = (
                round((approved_count / total_decisions) * 100, 2)
                if total_decisions > 0
                else 0
            )

            data = {
                # ── EVERYONE SEES THIS ────────────────────────────
                # answers: "what is the state of my requests?"
                "my_expenses": {
                    "total": my_expenses.count(),
                    "pending": my_expenses.filter(status__code="pending").count(),
                    "approved": my_expenses.filter(status__code="approved").count(),
                    "rejected": my_expenses.filter(status__code="rejected").count(),
                    "disbursed": my_expenses.filter(status__code="disbursed").count(),
                    "completed": my_expenses.filter(status__code="completed").count(),
                    # answers: "do i have any unsubmitted reconciliations?"
                    "my_pending_reconciliations": DisbursementReconciliationService()
                    .filter(submitted_by=auth_user, status__code="pending")
                    .count(),
                    # answers: "what just happened on my account?"
                    "my_recent_activities": list(
                        TransactionLogService()
                        .filter(triggered_by=auth_user)
                        .select_related("event_type__event_category")
                        .values(
                            "event_type__name",
                            "event_type__code",
                            "event_type__status_code",
                            "event_type__description",
                            "event_message",
                            "entity_type",
                            "entity_id",
                            "created_at",
                        )
                        .order_by("-created_at")[:5]
                    ),
                },
                # ── FO / CFO / ADM SEES THIS ──────────────────────
                # answers: "what needs my action right now?"
                "actions_required": {
                    "expenses_pending_review": ExpenseRequestService()
                    .filter(is_active=True, status__code="pending")
                    .count(),
                    "reconciliation_pending_review": DisbursementReconciliationService()
                    .filter(is_active=True, status__code="under_review")
                    .count(),
                    "topup_pending_approvals": TopUpRequestService()
                    .filter(is_active=True, status__code="pending")
                    .count(),
                },
                # ── CFO / ADM SEES THIS ───────────────────────────
                # answers: "is the petty cash account healthy?"
                "petty_cash_balance": {
                    "total_balance": PettyCashAccountService()
                    .filter(is_active=True)
                    .aggregate(total=Sum("current_balance"))["total"]
                    or 0
                },
                "total_disbursed_this_month": ExpenseRequestService()
                .filter(
                    is_active=True,
                    status__code="disbursed",
                    created_at__gte=month_start,
                )
                .aggregate(total=Sum("amount"))["total"]
                or 0,
            }
            return ResponseProvider().success(data=data)
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)
