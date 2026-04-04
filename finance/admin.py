from django.contrib import admin
from finance.models import (
    DisbursementReconciliation,
    ExpenseRequest,
    LoanConfig,
    LoanRequest,
    MpesaTransactionCost,
    PettyCashAccount,
    TopUpRequest,
)


@admin.register(PettyCashAccount)
class PettyCashAccountAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "account_type",
        "mpesa_phone_number",
        "current_balance",
        "minimum_threshold",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "account_type")
    search_fields = ("name", "mpesa_phone_number")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(ExpenseRequest)
class ExpenseRequestAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "employee",
        "get_department",
        "expense_type",
        "amount",
        "status",
        "event_type",
        "category",
        "is_active",
        "created_at",
    )
    list_filter = ("expense_type", "status", "category", "event_type")
    search_fields = ("title", "employee__email", "employee__first_name", "employee__last_name", "mpesa_phone")
    readonly_fields = ("created_at", "updated_at", "metadata")
    raw_id_fields = ("employee",)
    ordering = ("-created_at",)

    @admin.display(description="Department")
    def get_department(self, obj):
        # derive department from employee as per the model comment
        return getattr(obj.employee, "department", None)


@admin.register(TopUpRequest)
class TopUpRequestAdmin(admin.ModelAdmin):
    list_display = (
        "pettycash_account",
        "requested_by",
        "decision_by",
        "amount",
        "status",
        "event_type",
        "is_auto_triggered",
        "created_at",
    )
    list_filter = ("status", "is_auto_triggered", "event_type")
    search_fields = (
        "requested_by__email",
        "requested_by__first_name",
        "decision_by__email",
        "pettycash_account__name",
    )
    readonly_fields = ("created_at", "updated_at", "metadata")
    raw_id_fields = ("requested_by", "decision_by", "pettycash_account")
    ordering = ("-created_at",)


@admin.register(DisbursementReconciliation)
class DisbursementReconciliationAdmin(admin.ModelAdmin):
    list_display = (
        "expense_request",
        "submitted_by",
        "approved_by",
        "reconciled_amount",
        "surplus_returned",
        "status",
        "submitted_at",
        "approved_at",
    )
    list_filter = ("status",)
    search_fields = (
        "submitted_by__email",
        "approved_by__email",
        "expense_request__title",
    )
    readonly_fields = ("submitted_at", "created_at", "updated_at", "metadata")
    raw_id_fields = ("expense_request", "submitted_by", "approved_by")
    ordering = ("-submitted_at",)


@admin.register(MpesaTransactionCost)
class MpesaTransactionCostAdmin(admin.ModelAdmin):
    list_display = ("min_amount", "max_amount", "cost", "is_active", "created_at")
    list_filter = ("is_active",)
    ordering = ("min_amount",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(LoanConfig)
class LoanConfigAdmin(admin.ModelAdmin):
    list_display = ("max_loan_amount", "is_active", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(LoanRequest)
class LoanRequestAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "amount",
        "status",
        "decision_by",
        "due_date",
        "repaid_at",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = (
        "employee__email",
        "employee__first_name",
        "employee__last_name",
        "decision_by__email",
    )
    readonly_fields = ("created_at", "updated_at", "metadata", "repaid_at")
    raw_id_fields = ("employee", "decision_by")
    ordering = ("-created_at",)