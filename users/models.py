from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random
from django.core.mail import send_mail
from .tasks import send_login_otp
import os

class UserManager(BaseUserManager):
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


class User(AbstractUser):
    """
    Custom User model for CheckMate-Central.
    Supports email-based login and roles (College, Staff).
    """
    class Role(models.TextChoices):
        COLLEGE = "COLLEGE", "College"
        STAFF = "STAFF", "Staff"

    base_role = Role.STAFF

    # Remove username, use email as unique identifier
    username = None
    email = models.EmailField(unique=True)

    # Groups and permissions (avoid clashes with AbstractUser)
    groups = models.ManyToManyField(
        Group,
        related_name="user_groups",
        blank=True,
        help_text="Groups this admin belongs to."
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="user_permissions_set",
        blank=True,
        help_text="Specific permissions for this admin."
    )

    # Passkeys for WebAuthn / FIDO2 (list of registered devices)
    passkey_devices = models.JSONField(default=list, blank=True)

    # Optional field to store challenges during WebAuthn authentication
    passkey_challenge = models.CharField(max_length=512, blank=True, null=True)

    role = models.CharField(max_length=50, choices=Role.choices, default=base_role)
    college = models.ForeignKey(
        'colleges.College',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users'
    )

    # Email is the login field
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # no other fields required for creation

    # Use the custom manager
    objects = UserManager()

    def __str__(self):
        return self.email
    
    @property
    def fullname(self):
        return self.get_full_name()

class LoginOTP(models.Model):
    """
    Stores a temporary OTP for CentralAdmin login.
    """
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    resend_attempts = models.PositiveIntegerField(default=0)
    last_resend_at = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        return timezone.now() <= self.expires_at

    def can_resend(self):
        if self.resend_attempts >= 5:
            return False, "You have reached the maximum number of resend attempts."
        if self.last_resend_at and timezone.now() < self.last_resend_at + timedelta(seconds=60):
            return False, "Please wait before requesting another OTP."
        return True, ""

    @staticmethod
    def generate_for_user(user: User, is_resend=False):
        """Create a new OTP for the given user, or update the existing one if resending."""
        otp_code = f"{random.randint(100000, 999999)}"
        expires = timezone.now() + timedelta(minutes=5)

        if is_resend:
            otp_obj = LoginOTP.objects.filter(user=user).last()
            if otp_obj:
                otp_obj.otp = otp_code
                otp_obj.expires_at = expires
                otp_obj.last_resend_at = timezone.now()
                otp_obj.resend_attempts += 1
                otp_obj.save()
            else:
                otp_obj = LoginOTP.objects.create(
                    user=user, otp=otp_code, expires_at=expires
                )
        else:
            # First OTP, clean old ones
            LoginOTP.objects.filter(user=user).delete()
            otp_obj = LoginOTP.objects.create(user=user, otp=otp_code, expires_at=expires)

        try:
            send_login_otp.delay(user.email, otp_code)
        except Exception as e:
            print(f"[WARN] Failed to send OTP email: {e}")

        if os.getenv('DEBUG', 'False') == 'True':
            print(f"[DEBUG] OTP for {user.email}: {otp_code}")
        return otp_obj
