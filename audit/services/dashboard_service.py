from django.db.models.functions import TruncMonth, TruncDay
from utils.response_provider import ResponseProvider
from django.db.models import Count, Sum
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
            month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_30_days = today - timedelta(days=30)
            last_6_months = today - timedelta(days=180)
            auth_user = request.user

            # ── Base querysets ────────────────────────────────────
            all_expenses = ExpenseRequestService().filter(is_active=True)
            my_expenses = ExpenseRequestService().filter(is_active=True, employee=auth_user)
            all_reconciliations = DisbursementReconciliationService().filter(is_active=True)
            my_reconciliations = DisbursementReconciliationService().filter(
                is_active=True, submitted_by=auth_user
            )

            # ── Approval rate this month ──────────────────────────
            approved_count = TransactionLogService().filter(
                event_type__code="expense_approved", created_at__gte=month_start
            ).count()

            rejected_count = TransactionLogService().filter(
                event_type__code="expense_rejected", created_at__gte=month_start
            ).count()

            total_decisions = approved_count + rejected_count
            approval_rate = (
                round((approved_count / total_decisions) * 100, 2)
                if total_decisions > 0 else 0
            )

            # ── Monthly expense trend (last 6 months) ────────────
            monthly_trend = list(
                all_expenses.filter(created_at__gte=last_6_months)
                .annotate(month=TruncMonth("created_at"))
                .values("month")
                .annotate(
                    total=Count("id"),
                    total_amount=Sum("amount"),
                    approved=Count("id", filter=__import__("django.db.models", fromlist=["Q"]).Q(status__code="approved")),
                    disbursed=Count("id", filter=__import__("django.db.models", fromlist=["Q"]).Q(status__code="disbursed")),
                )
                .order_by("month")
            )

            # format month for JSON
            for entry in monthly_trend:
                entry["month"] = entry["month"].strftime("%b %Y")
                entry["total_amount"] = str(entry["total_amount"] or 0)

            # ── Daily spend last 30 days ──────────────────────────
            daily_spend = list(
                all_expenses.filter(
                    created_at__gte=last_30_days,
                    status__code__in=["disbursed", "completed"]
                )
                .annotate(day=TruncDay("created_at"))
                .values("day")
                .annotate(total_amount=Sum("amount"))
                .order_by("day")
            )

            for entry in daily_spend:
                entry["day"] = entry["day"].strftime("%d %b")
                entry["total_amount"] = str(entry["total_amount"] or 0)

            # ── Expense breakdown by type ─────────────────────────
            expense_type_breakdown = {
                "disbursement": all_expenses.filter(expense_type="disbursement").count(),
                "reimbursement": all_expenses.filter(expense_type="reimbursement").count(),
            }

            # ── Petty cash health ─────────────────────────────────
            petty_cash = PettyCashAccountService().filter(is_active=True).first()
            petty_cash_data = None
            if petty_cash:
                is_low = petty_cash.current_balance <= petty_cash.minimum_threshold
                petty_cash_data = {
                    "id": str(petty_cash.id),
                    "name": petty_cash.name,
                    "current_balance": str(petty_cash.current_balance),
                    "minimum_threshold": str(petty_cash.minimum_threshold),
                    "is_low": is_low,
                    "account_type": petty_cash.account_type,
                    "mpesa_phone_number": petty_cash.mpesa_phone_number,
                }

            # ── Top-up summary ────────────────────────────────────
            topup_summary = {
                "total": TopUpRequestService().filter(is_active=True).count(),
                "pending": TopUpRequestService().filter(is_active=True, status__code="pending").count(),
                "approved": TopUpRequestService().filter(is_active=True, status__code="approved").count(),
                "completed": TopUpRequestService().filter(is_active=True, status__code="completed").count(),
                "total_disbursed_this_month": str(
                    TopUpRequestService()
                    .filter(is_active=True, status__code="completed", created_at__gte=month_start)
                    .aggregate(total=Sum("amount"))["total"] or 0
                ),
            }

            data = {
                # ── My expenses — every user ──────────────────────
                "my_expenses": {
                    "total": my_expenses.count(),
                    "pending": my_expenses.filter(status__code="pending").count(),
                    "approved": my_expenses.filter(status__code="approved").count(),
                    "rejected": my_expenses.filter(status__code="rejected").count(),
                    "disbursed": my_expenses.filter(status__code="disbursed").count(),
                    "completed": my_expenses.filter(status__code="completed").count(),
                    "total_amount_this_month": str(
                        my_expenses.filter(created_at__gte=month_start)
                        .aggregate(total=Sum("amount"))["total"] or 0
                    ),
                },

                # ── My reconciliations — every user ───────────────
                "my_reconciliations": {
                    "total": my_reconciliations.count(),
                    "pending": my_reconciliations.filter(status__code="pending").count(),
                    "under_review": my_reconciliations.filter(status__code="under_review").count(),
                    "completed": my_reconciliations.filter(status__code="completed").count(),
                    "rejected": my_reconciliations.filter(status__code="rejected").count(),
                },

                # ── All expenses — org wide ───────────────────────
                "all_expenses": {
                    "total": all_expenses.count(),
                    "pending": all_expenses.filter(status__code="pending").count(),
                    "approved": all_expenses.filter(status__code="approved").count(),
                    "rejected": all_expenses.filter(status__code="rejected").count(),
                    "disbursed": all_expenses.filter(status__code="disbursed").count(),
                    "completed": all_expenses.filter(status__code="completed").count(),
                    "total_disbursed_this_month": str(
                        all_expenses.filter(
                            status__code__in=["disbursed", "completed"],
                            created_at__gte=month_start,
                        ).aggregate(total=Sum("amount"))["total"] or 0
                    ),
                    "total_disbursed_all_time": str(
                        all_expenses.filter(status__code__in=["disbursed", "completed"])
                        .aggregate(total=Sum("amount"))["total"] or 0
                    ),
                    "approval_rate_this_month": approval_rate,
                    "type_breakdown": expense_type_breakdown,
                },

                # ── All reconciliations — org wide ────────────────
                "all_reconciliations": {
                    "total": all_reconciliations.count(),
                    "pending": all_reconciliations.filter(status__code="pending").count(),
                    "under_review": all_reconciliations.filter(status__code="under_review").count(),
                    "completed": all_reconciliations.filter(status__code="completed").count(),
                    "rejected": all_reconciliations.filter(status__code="rejected").count(),
                },

                # ── Actions required ──────────────────────────────
                "actions_required": {
                    "expenses_pending_review": all_expenses.filter(status__code="pending").count(),
                    "reconciliations_pending_review": all_reconciliations.filter(status__code="under_review").count(),
                    "topups_pending_approval": TopUpRequestService().filter(is_active=True, status__code="pending").count(),
                    "topups_approved_pending_disburse": TopUpRequestService().filter(is_active=True, status__code="approved").count(),
                },

                # ── Petty cash ────────────────────────────────────
                "petty_cash": petty_cash_data,

                # ── Top-up summary ────────────────────────────────
                "topup_summary": topup_summary,

                # ── Charts ────────────────────────────────────────
                "charts": {
                    "monthly_expense_trend": monthly_trend,
                    "daily_spend_last_30_days": daily_spend,
                },

                # ── Recent activity ───────────────────────────────
                "recent_activity": list(
                    TransactionLogService()
                    .filter(triggered_by=auth_user)
                    .select_related("event_type__event_category")
                    .values(
                        "event_type__name",
                        "event_type__code",
                        "event_message",
                        "entity_type",
                        "entity_id",
                        "created_at",
                    )
                    .order_by("-created_at")[:10]
                ),
            }

            # format recent_activity dates
            for activity in data["recent_activity"]:
                activity["created_at"] = activity["created_at"].isoformat()

            return ResponseProvider().success(data=data)

        except Exception as ex:
            return ResponseProvider.handle_exception(ex)