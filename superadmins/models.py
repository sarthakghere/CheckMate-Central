from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random


class CentralAdminManager(BaseUserManager):
    """Custom manager for CentralAdmin model with no username field."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CentralAdmin(AbstractUser):
    """
    CentralAdmin is the main admin for CheckMate-Central.
    Supports email-based login, password, optional passkey devices, and can be extended
    for future features like OTP login.
    """

    # Remove username, use email as unique identifier
    username = None
    email = models.EmailField(unique=True)

    # Groups and permissions (avoid clashes with AbstractUser)
    groups = models.ManyToManyField(
        Group,
        related_name="centraladmin_groups",
        blank=True,
        help_text="Groups this admin belongs to."
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="centraladmin_permissions",
        blank=True,
        help_text="Specific permissions for this admin."
    )

    # Passkeys for WebAuthn / FIDO2 (list of registered devices)
    passkey_devices = models.JSONField(default=list, blank=True)

    # Optional field to store challenges during WebAuthn authentication
    passkey_challenge = models.CharField(max_length=512, blank=True, null=True)

    # Email is the login field
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # no other fields required for creation

    # Use the custom manager
    objects = CentralAdminManager()

    def __str__(self):
        return self.email

class LoginOTP(models.Model):
    """
    Stores a temporary OTP for CentralAdmin login.
    """
    user = models.ForeignKey("CentralAdmin", on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return timezone.now() <= self.expires_at

    @staticmethod
    def generate_for_user(user):
        """Create a new OTP for the given user."""
        otp_code = f"{random.randint(100000, 999999)}"
        expires = timezone.now() + timedelta(minutes=5)
        otp_obj = LoginOTP.objects.create(user=user, otp=otp_code, expires_at=expires)
        # Here you can send OTP via email/SMS
        print(f"Generated OTP for {user.email}: {otp_code}")
        return otp_obj
