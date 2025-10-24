from django.contrib import admin
from django.utils.html import format_html
from rest_framework_api_key.models import APIKey
from .models import College

@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "api_key_display",
        "created_at",
        "updated_at",
    )
    search_fields = ("name", "code", "api_key__name")
    readonly_fields = ("created_at", "updated_at")
    list_filter = ("created_at",)

    fieldsets = (
        ("College Details", {
            "fields": ("name", "code"),
        }),
        ("API Access", {
            "fields": ("api_key",),
            "description": "Each college has a unique API key for authentication with external services."
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    def api_key_display(self, obj):
        """Show a partially masked API key name for safety."""
        if obj.api_key:
            key_name = obj.api_key.name
            return format_html('<b>{}</b>', key_name)
        return format_html('<span style="color:gray;">No API Key</span>')
    api_key_display.short_description = "API Key"

    def save_model(self, request, obj, form, change):
        """Auto-create an API key for new colleges if not assigned."""
        if not obj.api_key:
            key_name = f"{obj.code}_key"
            api_key, key = APIKey.objects.create_key(name=key_name)
            obj.api_key = api_key
            # Optionally display the generated key in admin logs
            self.message_user(request, f"API Key generated for {obj.name}: {key}", level="info")
        super().save_model(request, obj, form, change)
