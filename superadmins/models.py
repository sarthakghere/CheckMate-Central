from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class SuperAdmin(AbstractUser):
    email = models.EmailField(unique=True)

    # Override groups and user_permissions to avoid reverse accessor clash
    groups = models.ManyToManyField(
        Group,
        related_name="superadmin_groups",  # unique related_name
        blank=True,
        help_text="Groups this superadmin belongs to."
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="superadmin_permissions",  # unique related_name
        blank=True,
        help_text="Specific permissions for this superadmin."
    )

    # Passkeys for WebAuthn / FIDO2
    passkey_devices = models.JSONField(default=list, blank=True)
    otp_secret = models.CharField(max_length=32, blank=True, null=True)

    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.email
