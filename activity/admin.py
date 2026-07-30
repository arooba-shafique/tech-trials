from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'action', 'model_name', 'object_repr',
        'ip_address', 'path', 'timestamp'
    )
    list_filter = ('action', 'timestamp', 'model_name')
    search_fields = ('user__username', 'model_name', 'object_repr', 'ip_address', 'path')
    readonly_fields = (
        'user', 'action', 'model_name', 'object_id', 'object_repr',
        'field_name', 'old_value', 'new_value', 'ip_address',
        'user_agent', 'path', 'method', 'details', 'timestamp'
    )
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
