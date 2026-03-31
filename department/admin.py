from django.contrib import admin
from department.models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "description", "line_manager", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name", "line_manager__email", "line_manager__first_name", "line_manager__last_name")
    ordering = ("code",)
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("line_manager",)