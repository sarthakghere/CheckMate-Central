from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from users.models import User
from colleges.models import College
from university.models import University
from rest_framework_api_key.models import APIKey
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)


def get_user_info(request):
    """Return formatted user info string for logging."""
    if hasattr(request, "user") and request.user.is_authenticated:
        return f"{request.user.email} (Role: {getattr(request.user, 'role', 'UNKNOWN')})"
    return "Anonymous user"


@login_required
def college_dashboard(request):
    user_info = get_user_info(request)
    college = request.user.college  # assuming user is a college user

    logger.info(f"Dashboard viewed by {user_info} for {college.name} ({college.code})")

    users = college.users.all()
    backups = college.backups.all().order_by('-uploaded_at')

    return render(request, 'colleges/dashboard.html', {
        'college': college,
        'users': users,
        'backups': backups,
    })


@login_required
def register_college(request):
    user_info = get_user_info(request)

    if request.user.role != User.Role.STAFF:
        logger.warning(f"Unauthorized college registration attempt by {user_info}")
        return redirect("colleges:college_dashboard")

    if request.method == "POST":
        name = request.POST.get("name")
        code = request.POST.get("code")

        if request.user.is_staff_user:
            uni_code = request.POST.get("uni_code")
            university = get_object_or_404(University, code=uni_code)
        else:
            university = request.user.university

        college = College.objects.create(name=name, code=code, university=university)
        logger.info(f"New college registered: {college.name} ({college.code}) by {user_info}")

        names = request.POST.getlist("names[]")
        emails = request.POST.getlist("emails[]")
        passwords = request.POST.getlist("passwords[]")

        for name, email, password in zip(names, emails, passwords):
            if name and email and password:
                first_name = name.split()[0]
                last_name = " ".join(name.split()[1:]) if len(name.split()) > 1 else ""
                User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role=User.Role.COLLEGE,
                    college=college
                )
                logger.info(f"User {email} ({name}) added to college {college.code} by {user_info}")

        messages.success(request, f"College '{college.name}' and its users registered successfully.")
        return redirect("users:staff_dashboard")

    logger.info(f"College registration form viewed by {user_info}")
    return render(request, "colleges/register_college.html")


@login_required
def manage_college(request, college_id):
    college = get_object_or_404(College, id=college_id)
    users = User.objects.filter(college=college, role=User.Role.COLLEGE)

    if request.user.role not in (User.Role.STAFF, User.Role.UNIVERSITY):
        return redirect("colleges:dashbaord")

    # Update college info
    if "update_college" in request.POST:
        college.name = request.POST.get("name")
        college.code = request.POST.get("code")
        college.save()
        messages.success(request, "College info updated successfully.")
        return redirect("colleges:manage_college", college_id=college.id)

    # Remove user
    if "remove_user" in request.POST:
        user = get_object_or_404(User, id=request.POST.get("user_id"), college=college)
        user.delete()
        messages.success(request, f"User {user.email} removed successfully.")
        return redirect("colleges:manage_college", college_id=college.id)

    # Edit user
    if "edit_user" in request.POST:
        user = get_object_or_404(User, id=request.POST.get("user_id"), college=college)
        user.email = request.POST.get("email")
        name = request.POST.get("name")
        if name:
            user.first_name = name  # store full name in first_name for simplicity
        password = request.POST.get("password")
        if password:
            user.set_password(password)
        user.save()
        messages.success(request, f"User {user.email} updated successfully.")
        return redirect("colleges:manage_college", college_id=college.id)

    # Add new user
    if "add_user" in request.POST:
        email = request.POST.get("email")
        password = request.POST.get("password")
        name = request.POST.get("name")
        first_name = name.split()[0]
        last_name = " ".join(name.split()[1:]) if len(name.split()) > 1 else ""
        if email and password and name:
            User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=User.Role.COLLEGE,
                college=college
            )
            messages.success(request, f"User {email} added successfully.")
        return redirect("colleges:manage_college", college_id=college.id)

    return render(request, "colleges/manage_college.html", {"college": college, "users": users})


@login_required
def reset_api_key(request, college_id):
    user_info = get_user_info(request)

    college = get_object_or_404(College, id=college_id)
    current_key = (college.api_key.prefix + ".......") if college.api_key else None
    new_key = None

    if request.method == "POST":
        if college.api_key:
            college.api_key.delete()
            logger.info(f"Old API key deleted for {college.name} ({college.code}) by {user_info}")

        api_key_obj, key = APIKey.objects.create_key(name=f"{college.code}-key")
        college.api_key = api_key_obj
        college.save()
        new_key = key
        logger.info(f"New API key generated for {college.name} ({college.code}) by {user_info}")

    return render(request, "colleges/show_college_api_key.html", {
        "college": college,
        "current_key": current_key,
        "new_key": new_key
    })
