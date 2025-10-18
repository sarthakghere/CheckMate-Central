from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from users.models import User
from university.models import University
from colleges.models import College
from backups.models import Backup
from django.db.models import Max
from rest_framework_api_key.models import APIKey
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

def get_user_info(request):
    """Return formatted user info string for logging."""
    if hasattr(request, "user") and request.user.is_authenticated:
        return f"{request.user.email} (Role: {getattr(request.user, 'role', 'UNKNOWN')})"
    return "Anonymous user"

# Create your views here.
@login_required
def register_university(request):
    user_info = get_user_info(request)

    if request.user.role != User.Role.STAFF:
        logger.warning(f"Unauthorized university registration attempt by {user_info}")
        return redirect("university:university_dashboard")

    if request.method == "POST":
        name = request.POST.get("name")
        code = request.POST.get("code")

        university = University.objects.create(name=name, code=code)
        logger.info(f"New university registered: {university.name} ({university.code}) by {user_info}")

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
                    role=User.Role.UNIVERSITY,
                    university=university
                )
                logger.info(f"User {email} ({name}) added to university {university.code} by {user_info}")

        messages.success(request, f"University '{university.name}' and its users registered successfully.")
        return redirect("users:staff_dashboard")

    logger.info(f"university registration form viewed by {user_info}")
    return render(request, "university/register_university.html")

@login_required
def university_dashboard(request, university_id=None):
    if request.user.role not in (User.Role.UNIVERSITY, User.Role.STAFF):
        logger.warning(f"Unauthorized access attempt to staff dashboard by {request.user.email} ({request.user.role})")
        return redirect("users:college_dashboard")

    if request.user.role == User.Role.UNIVERSITY:
        university = request.user.university
    else:
        university = get_object_or_404(University, id=university_id)

    colleges = College.objects.filter(university=university).order_by("name").annotate(last_backup_time=Max('backups__uploaded_at'))
    total_backups = Backup.objects.count()
    total_colleges = colleges.count()

    logger.info(f"Staff dashboard accessed by {request.user.email}. Total colleges: {total_colleges}, backups: {total_backups}")
    return render(request, "university/dashboard.html", {
        "university": university,
        "colleges": colleges,
        "total_backups": total_backups,
        "total_colleges": total_colleges,
    })
