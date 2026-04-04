from django.contrib import admin
from audit.models import TransactionLogBase, Notifications, EventTypes


@admin.register(EventTypes)
class EventTypesAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "event_category", "is_active", "status_code")
    list_filter = ("is_active", "event_category")
    search_fields = ("code", "name")
    ordering = ("code",)


@admin.register(TransactionLogBase)
class TransactionLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "event_type",
        "get_event_category",
        "status",
        "triggered_by",
        "entity_type",
        "entity_id",
        "event_message",
        "user_ip_address",
        "created_at",
    )
    list_filter = ("status", "event_type__event_category", "entity_type")
    search_fields = ("entity_id", "entity_type", "event_message", "triggered_by__email")
    readonly_fields = ("created_at", "user_ip_address", "metadata")
    ordering = ("-created_at",)

    @admin.display(description="Event Category")
    def get_event_category(self, obj):
        return obj.event_type.event_category


@admin.register(Notifications)
class NotificationsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "recipient",
        "get_event_type",
        "get_entity_id",
        "channel",
        "is_read",
        "read_at",
        "created_at",
    )
    list_filter = ("channel", "is_read")
    search_fields = ("recipient__email", "transaction_log__entity_id")
    readonly_fields = ("read_at", "created_at")
    ordering = ("-created_at",)

    @admin.display(description="Event Type")
    def get_event_type(self, obj):
        return obj.transaction_log.event_type.code

    @admin.display(description="Entity ID")
    def get_entity_id(self, obj):
        return obj.transaction_log.entity_id