from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from users.models import User
from colleges.models import College
from rest_framework_api_key.models import APIKey
from django.contrib import messages

@login_required
def college_dashboard(request):
    return render(request, "colleges/college_dashboard.html")

@login_required
def register_college(request):
    if request.user.role != User.Role.STAFF:
        return redirect("colleges:college_dashboard")

    if request.method == "POST":
        name = request.POST.get("name")
        code = request.POST.get("code")

        # Create College
        college = College.objects.create(name=name, code=code)

        # Create multiple users
        emails = request.POST.getlist("emails[]")
        passwords = request.POST.getlist("passwords[]")

        for email, password in zip(emails, passwords):
            if email and password:
                User.objects.create_user(
                    email=email,
                    password=password,
                    role=User.Role.COLLEGE,
                    college=college
                )

        return redirect("users:staff_dashboard")

    return render(request, "colleges/register_college.html")

@login_required
def manage_college(request, college_id):
    if request.user.role != User.Role.STAFF:
        return redirect("colleges:college_dashboard")

    college = get_object_or_404(College, id=college_id)

    # --------------------------
    # Update College Info
    # --------------------------
    if request.method == "POST" and "update_college" in request.POST:
        name = request.POST.get("name")
        code = request.POST.get("code")
        if name and code:
            college.name = name
            college.code = code
            college.save()
            messages.success(request, "College information updated successfully.")
        return redirect("colleges:manage_college", college_id=college.id)

    # --------------------------
    # Add New User
    # --------------------------
    if request.method == "POST" and "add_user" in request.POST:
        email = request.POST.get("email")
        password = request.POST.get("password")
        if email and password:
            User.objects.create_user(
                email=email,
                password=password,
                role=User.Role.COLLEGE,
                college=college
            )
            messages.success(request, f"User {email} added successfully.")
        return redirect("colleges:manage_college", college_id=college.id)

    # --------------------------
    # Edit Existing User
    # --------------------------
    if request.method == "POST" and "edit_user" in request.POST:
        user_id = request.POST.get("user_id")
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = User.objects.filter(id=user_id, college=college).first()
        if user:
            user.email = email
            if password:
                user.set_password(password)
            user.save()
            messages.success(request, f"User {email} updated successfully.")
        return redirect("colleges:manage_college", college_id=college.id)

    # --------------------------
    # Remove User
    # --------------------------
    if request.method == "POST" and "remove_user" in request.POST:
        user_id = request.POST.get("user_id")
        user = User.objects.filter(id=user_id, college=college).first()
        if user:
            user.delete()
            messages.success(request, f"User {user.email} removed successfully.")
        return redirect("colleges:manage_college", college_id=college.id)

    return render(request, "colleges/manage_college.html", {
        "college": college,
        "users": college.users.all(),
    })


@login_required
def reset_api_key(request, college_id):
    # Only staff can access
    if request.user.role != User.Role.STAFF:
        return redirect("colleges:college_dashboard")

    college = get_object_or_404(College, id=college_id)

    current_key = (college.api_key.prefix + ".......") if college.api_key else None
    new_key = None

    if request.method == "POST":
        # Regenerate API key
        if college.api_key:
            college.api_key.delete()  # remove old key

        api_key_obj, key = APIKey.objects.create_key(name=f"{college.code}-key")
        college.api_key = api_key_obj
        college.save()
        new_key = key

    return render(request, "colleges/show_college_api_key.html", {
        "college": college,
        "current_key": current_key,
        "new_key": new_key
    })
