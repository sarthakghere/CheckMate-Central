from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from users.models import User, CreatePasswordRequest
from colleges.models import College
from rest_framework_api_key.models import APIKey
from django.contrib import messages
from .forms import RegisterCollegeForm, RegisterCollegeUserForm, CreateCollegeUserPasswordForm
import logging

logger = logging.getLogger(__name__)


def get_user_info(request):
    """Return formatted user info string for logging."""
    if hasattr(request, "user") and request.user.is_authenticated:
        return f"{request.user.email} (Role: {getattr(request.user, 'role', 'UNKNOWN')})"
    return "Anonymous user"

def get_user_role(request):
    """Return the role of the logged-in user."""
    if hasattr(request, "user") and request.user.is_authenticated:
        if request.user.role == User.Role.STAFF:
            return User.Role.STAFF
        elif request.user.role == User.Role.COLLEGE:
            return User.Role.COLLEGE

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

    if get_user_role(request) != User.Role.STAFF:
        logger.warning(f"Unauthorized college registration attempt by {user_info}")
        return redirect("colleges:college_dashboard")

    if request.method == "POST":
        form = RegisterCollegeForm(request.POST)
        if form.is_valid():
            college = form.save()
            messages.success(request, f"College '{college.name}' registered successfully.")
            logger.info(f"New college registered: {college.name} ({college.code}) by {user_info}")
            return redirect("users:staff_dashboard")
        else:
            logger.warning(f"Invalid college registration attempt by {user_info}: {form.errors.as_text()}")
    else:
        form = RegisterCollegeForm()
        logger.info(f"College registration form viewed by {user_info}")

    return render(request, "colleges/register_college.html", {"form": form})

@login_required
def register_college_user(request, college_id):
    user_info = get_user_info(request)
    college = get_object_or_404(College, id=college_id)

    if get_user_role(request) != User.Role.STAFF:
        logger.warning(f"Unauthorized college user registration attempt by {user_info}")
        return redirect("colleges:college_dashboard")

    if request.method == "POST":
        form = RegisterCollegeUserForm(request.POST)
        if form.is_valid():
            user: User = form.save(commit=False)
            user.role = User.Role.COLLEGE
            user.college = college
            user.set_unusable_password()
            user.save()
            CreatePasswordRequest.objects.create(user=user, college=college)
            messages.success(request, f"College user {user.fullname} for college '{college.name}' registered successfully.")
            logger.info(f"New college user registered: {user.fullname} ({user.email}) by {user_info}")
            return redirect("users:staff_dashboard")
        else:
            logger.warning(f"Invalid college user registration attempt by {user_info}: {form.errors.as_text()}")
    else:
        form = RegisterCollegeUserForm()
        logger.info(f"College user registration form viewed by {user_info}")

    return render(request, "colleges/register_college_user.html", {"form": form})

def create_college_user_password(request, user_id):
    user = get_object_or_404(User, id=user_id, role=User.Role.COLLEGE)
    create_password_request = get_object_or_404(CreatePasswordRequest, user=user)
    if create_password_request.is_complete:
        messages.info(request, "This password creation link has already been used. Contact support if you need assistance.")
        return redirect("users:login")
    else:
        if request.method == "POST":
            form = CreateCollegeUserPasswordForm(request.POST)
            if form.is_valid():
                password = form.cleaned_data['password1']
                user.set_password(password)
                user.save()
                create_password_request.is_complete = True
                create_password_request.save()
                messages.success(request, f"Password set successfully for user {user.fullname}.")
                logger.info(f"Password set for college user: {user.fullname} ({user.email})")
                return redirect("users:login")
            else:
                logger.warning(f"Invalid password creation attempt: {form.errors.as_text()}")
        else:
            form = CreateCollegeUserPasswordForm()
            logger.info(f"Password creation form viewed for user {user.fullname} ({user.email})")

    return render(request, "colleges/create_college_user_password.html", {"form": form, "user": user})

@login_required
def manage_college(request, college_id):

    if get_user_role(request) != User.Role.STAFF:
        return redirect("colleges:college_dashboard")

    college = get_object_or_404(College, id=college_id)
    users = User.objects.filter(college=college, role=User.Role.COLLEGE)

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
