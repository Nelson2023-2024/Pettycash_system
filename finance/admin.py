from django.contrib import admin
from finance.models import ExpenseRequest,TopUpRequest,PettyCashAccount,DisbursementReconciliation

# Register your models here.

admin.site.register(PettyCashAccount)
admin.site.register(ExpenseRequest)
admin.site.register(TopUpRequest)
admin.site.register(DisbursementReconciliation)
