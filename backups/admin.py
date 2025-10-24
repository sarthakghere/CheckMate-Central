from django.contrib import admin
from django.utils.html import format_html
from .models import Backup

@admin.register(Backup)
class BackupAdmin(admin.ModelAdmin):
    list_display = (
        "college",
        "uploaded_at",
        "file_link",
        "file_size_display",
        "short_checksum",
    )
    list_filter = ("college", "uploaded_at")
    search_fields = ("college__name", "college__code", "remarks", "checksum")
    readonly_fields = (
        "uploaded_at",
        "file_size",
        "checksum",
    )
    fieldsets = (
        ("Backup Details", {
            "fields": ("college", "file", "remarks")
        }),
        ("Metadata", {
            "fields": ("uploaded_at", "file_size", "checksum"),
        }),
    )

    def file_link(self, obj):
        """Show download link for backup file."""
        if obj.file:
            return format_html('<a href="{}" target="_blank">Download</a>', obj.file.url)
        return "-"
    file_link.short_description = "File"

    def file_size_display(self, obj):
        """Display file size in readable format."""
        if obj.file_size:
            size_kb = obj.file_size / 1024
            return f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb / 1024:.2f} MB"
        return "-"
    file_size_display.short_description = "Size"

    def short_checksum(self, obj):
        """Show shortened checksum for quick viewing."""
        if obj.checksum:
            return f"{obj.checksum[:12]}..."
        return "-"
    short_checksum.short_description = "Checksum"

    def has_delete_permission(self, request, obj=None):
        """Optional: restrict deletion to superusers."""
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        """Attach remarks about who uploaded the backup."""
        if not obj.remarks:
            obj.remarks = f"Uploaded by {request.user.email or request.user.username}"
        super().save_model(request, obj, form, change)
