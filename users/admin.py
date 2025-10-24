from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import User, CreatePasswordRequest, LoginOTP


# ----------------------------- #
# 🧑‍💻  USER ADMIN CONFIGURATION
# ----------------------------- #
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "fullname",
        "role",
        "college_display",
        "is_active",
        "is_staff",
        "created_at",
    )
    list_filter = ("role", "is_active", "is_staff", "college")
    search_fields = ("email", "first_name", "last_name", "college__name", "college__code")
    readonly_fields = ("created_at", "updated_at", "passkey_challenge")
    ordering = ("-created_at",)

    fieldsets = (
        ("User Information", {
            "fields": (
                "email",
                "first_name",
                "last_name",
                "role",
                "college",
            )
        }),
        ("Authentication Details", {
            "fields": (
                "password",
                "passkey_devices",
                "passkey_challenge",
            ),
            "description": "WebAuthn (FIDO2) device and challenge data."
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            ),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    def college_display(self, obj):
        if obj.college:
            return format_html('<b>{}</b>', obj.college.code)
        return format_html('<span style="color:gray;">—</span>')
    college_display.short_description = "College"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("college")

    def has_delete_permission(self, request, obj=None):
        # Prevent accidental deletion of admin users
        if obj and obj.is_superuser:
            return False
        return super().has_delete_permission(request, obj)


# ------------------------------------ #
# 🔑  CREATE PASSWORD REQUEST ADMIN
# ------------------------------------ #
@admin.register(CreatePasswordRequest)
class CreatePasswordRequestAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "college",
        "uuid",
        "is_complete",
        "is_expired_display",
        "created_at",
    )
    list_filter = ("is_complete", "college", "created_at")
    search_fields = ("user__email", "college__code", "uuid")
    readonly_fields = ("uuid", "created_at", "is_complete")

    def is_expired_display(self, obj):
        expired = obj.is_expired
        color = "red" if expired else "green"
        text = "Expired" if expired else "Valid"
        return format_html(f'<b style="color:{color};">{text}</b>')
    is_expired_display.short_description = "Status"


# ----------------------------- #
# 🔐  LOGIN OTP ADMIN
# ----------------------------- #
@admin.register(LoginOTP)
class LoginOTPAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "otp_masked",
        "expires_at",
        "resend_attempts",
        "valid_display",
    )
    list_filter = ("created_at", "expires_at")
    search_fields = ("user__email", "otp")
    readonly_fields = ("created_at", "expires_at", "resend_attempts", "last_resend_at")

    def otp_masked(self, obj):
        """Show OTP masked for security."""
        return f"•••{obj.otp[-3:]}" if obj.otp else "-"
    otp_masked.short_description = "OTP"

    def valid_display(self, obj):
        """Show color-coded validity status."""
        is_valid = obj.is_valid()
        color = "green" if is_valid else "red"
        status = "Valid" if is_valid else "Expired"
        return format_html(f"<b style='color:{color};'>{status}</b>")
    valid_display.short_description = "Validity"

    def has_add_permission(self, request):
        # Prevent manual creation of OTPs via admin
        return False
