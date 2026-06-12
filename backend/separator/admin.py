from django.contrib import admin

from separator.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "short_id",
        "status",
        "mode",
        "original_filename",
        "file_size_display",
        "created_at",
    )
    list_filter = ("status", "mode")
    search_fields = ("original_filename", "id")
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "completed_at",
        "error_message",
        "stems",
    )
    actions = ("mark_as_failed",)

    def short_id(self, obj):
        return str(obj.id)[:8]

    short_id.short_description = "ID"

    def file_size_display(self, obj):
        if obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        return f"{obj.file_size / (1024 * 1024):.1f} MB"

    file_size_display.short_description = "Size"

    @admin.action(description="Mark selected tasks as Failed")
    def mark_as_failed(self, request, queryset):
        count = queryset.filter(status=Task.Status.PROCESSING).update(
            status=Task.Status.FAILED,
            error_message="Manually marked as failed by admin",
        )
        self.message_user(request, f"Marked {count} tasks as failed")
