from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import User, LoginOTP

def landing_page(request, exception = None):
    if request.user.is_authenticated:
        if request.user.role == User.Role.STAFF:
            return redirect("users:staff_dashboard")
        elif request.user.role == User.Role.COLLEGE:
            return redirect("users:college_dashboard")
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
            # Generate OTP
            LoginOTP.generate_for_user(user)
            request.session["otp_user_id"] = user.id
            return redirect("users:otp_verify")
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
        return redirect("users:login")

    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        if otp_obj.otp == entered_otp:
            if otp_obj.is_valid():
                otp_obj.delete()  # consume OTP
                login(request, user)
                request.session.pop("otp_user_id", None)
                request.session.cycle_key()
                if user.role == User.Role.STAFF:
                    return redirect("users:staff_dashboard")
                elif user.role == User.Role.COLLEGE:
                    return redirect("users:college_dashboard")
            else:
                otp_obj.delete()
                return render(request, "users/otp_verify.html", {"error": "OTP expired"})
        else:
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

    try:
        user = User.objects.get(id=user_id)
        old_otp = LoginOTP.objects.filter(user=user).latest("created_at")
    except (User.DoesNotExist, LoginOTP.DoesNotExist):
        return redirect("users:login")

    can_resend, error_message = old_otp.can_resend()
    if not can_resend:
        return render(request, "users/otp_verify.html", {"error": error_message})

    # Generate a new OTP
    new_otp = LoginOTP.generate_for_user(user)
    
    # Carry over resend_attempts + last_resend_at
    new_otp.resend_attempts = old_otp.resend_attempts + 1
    new_otp.last_resend_at = timezone.now()
    new_otp.save()

    return redirect("users:otp_verify")


@login_required
def staff_dashboard(request):
    return render(request, "users/staff_dashboard.html")

@login_required
def college_dashboard(request):
    return render(request, "users/college_dashboard.html")

def user_logout(request):
    logout(request)
    return redirect("users:login")
