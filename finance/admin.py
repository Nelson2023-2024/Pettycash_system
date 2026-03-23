from django.contrib import admin
from finance.models import (DisbursementReconciliation, ExpenseRequest, LoanConfig, LoanRequest,
    MpesaTransactionCost, PettyCashAccount, TopUpRequest)
from users.models import User


class ExpenseRequestAdmin(admin.ModelAdmin):
    
    """
    Admin configuration for ExpenseRequest.
    Restricts the 'assigned_to' field to only show users with the
    Finance Officer (FO) role, preventing incorrect assignments.
    """
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'assigned_to':
            kwargs['queryset'] = User.objects.filter(
                role__code='FO',
                is_active=True
            ).select_related('role')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(PettyCashAccount)
admin.site.register(ExpenseRequest, ExpenseRequestAdmin)
admin.site.register(TopUpRequest)
admin.site.register(DisbursementReconciliation)

@admin.register(MpesaTransactionCost)
class MpesaTransactionCostAdmin(admin.ModelAdmin):
    list_display = ['min_amount', 'max_amount', 'cost', 'is_active']
    ordering = ['min_amount']
    
@admin.register(LoanConfig)
class LoanConfigAdmin(admin.ModelAdmin):
    list_display = ['max_loan_amount', 'is_active', 'created_at']

@admin.register(LoanRequest)
class LoanRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'amount', 'status', 'due_date', 'created_at']
    list_filter = ['status']