from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import CentralAdmin, LoginOTP

# -----------------------------
# Step 1: Email + Password
# -----------------------------
def email_password_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password)
        if user and user.is_active:
            # generate OTP for this login attempt
            LoginOTP.generate_for_user(user)
            # store user id temporarily in session for OTP verification
            request.session["otp_user_id"] = user.id
            return redirect("superadmin:otp_verify")
        else:
            return render(request, "superadmin/login.html", {"error": "Invalid credentials"})

    return render(request, "superadmin/login.html")


# -----------------------------
# Step 2: OTP Verification
# -----------------------------
def otp_verify(request):
    user_id = request.session.get("otp_user_id")
    if not user_id:
        return redirect("superadmin:login")

    user = CentralAdmin.objects.get(id=user_id)

    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        # check if OTP is valid
        try:
            otp_obj = LoginOTP.objects.get(user=user, otp=entered_otp)
            if otp_obj.is_valid():
                otp_obj.delete()  # consume OTP
                login(request, user)
                request.session.pop("otp_user_id", None)
                return redirect("superadmin:dashboard")
            else:
                otp_obj.delete()
                return render(request, "superadmin/otp_verify.html", {"error": "OTP expired"})
        except LoginOTP.DoesNotExist:
            return render(request, "superadmin/otp_verify.html", {"error": "Invalid OTP"})

    return render(request, "superadmin/otp_verify.html")

# TODO: Implement Admin Dashboard