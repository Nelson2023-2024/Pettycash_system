from django.contrib import admin
from audit.models import TransactionLogBase,Notifications,EventTypes,EventCategory

# Register your models here.
admin.site.register(EventCategory)
admin.site.register(EventTypes)
admin.site.register(TransactionLogBase)
admin.site.register(Notifications)