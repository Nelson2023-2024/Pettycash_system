from django.contrib import admin
from finance.models import ExpenseRequest,TopUpRequest,PettyCashAccount

# Register your models here.

admin.site.register(PettyCashAccount)
admin.site.register(ExpenseRequest)
admin.site.register(TopUpRequest)
