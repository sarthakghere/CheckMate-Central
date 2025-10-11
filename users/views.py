import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import User, LoginOTP
from colleges.models import College
from rest_framework_api_key.models import APIKey
from backups.models import Backup
from django.contrib import messages
from django.db.models import Max

logger = logging.getLogger(__name__)

def landing_page(request, exception=None):
    if request.user.is_authenticated:
        logger.info(f"Landing page accessed by authenticated user {request.user.email} ({request.user.role})")
        if request.user.role == User.Role.STAFF:
            return redirect("users:staff_dashboard")
        elif request.user.role == User.Role.COLLEGE:
            return redirect("colleges:college_dashboard")
    else:
        logger.info("Landing page accessed by unauthenticated user.")
    return redirect("users:login")


# -----------------------------
# Step 1: Email + Password
# -----------------------------
def email_password_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password)
        if user and user.is_active:
            LoginOTP.generate_for_user(user)
            request.session["otp_user_id"] = user.id
            logger.info(f"OTP generated for {email} ({user.role})")
            return redirect("users:otp_verify")
        else:
            logger.warning(f"Failed login attempt for email {email}")
            return render(request, "users/login.html", {"error": "Invalid credentials"})
    return render(request, "users/login.html")


# -----------------------------
# Step 2: OTP Verification
# -----------------------------
def otp_verify(request):
    user_id = request.session.get("otp_user_id")
    if not user_id:
        return redirect("users:login")

    try:
        user = User.objects.get(id=user_id)
        otp_obj = LoginOTP.objects.filter(user=user).latest("created_at")
    except (User.DoesNotExist, LoginOTP.DoesNotExist):
        logger.error("OTP verification attempted with invalid user or OTP record.")
        return redirect("users:login")

    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        if otp_obj.otp == entered_otp:
            if otp_obj.is_valid():
                otp_obj.delete()  # consume OTP
                login(request, user)
                request.session.pop("otp_user_id", None)
                request.session.cycle_key()
                logger.info(f"Successful OTP verification and login for {user.email} ({user.role})")
                if user.role == User.Role.STAFF:
                    return redirect("users:staff_dashboard")
                elif user.role == User.Role.COLLEGE:
                    return redirect("colleges:college_dashboard")
            else:
                otp_obj.delete()
                logger.warning(f"Expired OTP used by {user.email}")
                return render(request, "users/otp_verify.html", {"error": "OTP expired"})
        else:
            logger.warning(f"Invalid OTP attempt by {user.email}")
            return render(request, "users/otp_verify.html", {
                "error": "Invalid OTP",
                "remaining_attempts": 5 - otp_obj.resend_attempts
            })

    remaining_attempts = 5 - otp_obj.resend_attempts
    return render(request, "users/otp_verify.html", {"remaining_attempts": remaining_attempts})


# -----------------------------
# Step 3: Resend OTP
# -----------------------------
def resend_otp(request):
    user_id = request.session.get("otp_user_id")
    if not user_id:
        return redirect("users:login")

    user = get_object_or_404(User, id=user_id)
    otp_obj = LoginOTP.objects.filter(user=user).last()
    if not otp_obj:
        return redirect("users:login")

    can_resend, error_message = otp_obj.can_resend()
    if not can_resend:
        return render(request, "users/otp_verify.html", {"error": error_message})

    # generate a new OTP but mark it as a resend
    LoginOTP.generate_for_user(user, is_resend=True)
    return redirect("users:otp_verify")


def user_logout(request):
    if request.user.is_authenticated:
        logger.info(f"User {request.user.email} ({request.user.role}) logged out.")
    logout(request)
    return redirect("users:login")


@login_required
def staff_dashboard(request):
    if request.user.role != "STAFF":
        logger.warning(f"Unauthorized access attempt to staff dashboard by {request.user.email} ({request.user.role})")
        return redirect("users:college_dashboard")

    colleges = College.objects.all().order_by("name").annotate(last_backup_time=Max('backups__uploaded_at'))
    total_backups = Backup.objects.count()
    total_colleges = colleges.count()

    logger.info(f"Staff dashboard accessed by {request.user.email}. Total colleges: {total_colleges}, backups: {total_backups}")
    return render(request, "users/staff_dashboard.html", {
        "colleges": colleges,
        "total_backups": total_backups,
        "total_colleges": total_colleges,
    })
