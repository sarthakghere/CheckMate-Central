from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("login/", views.email_password_login, name="login"),
    path("otp-verify/", views.otp_verify, name="otp_verify"),
    path("resend-otp/", views.resend_otp, name="resend_otp"),
    path("dashboard/staff/", views.staff_dashboard, name="staff_dashboard"),
    path("dashboard/college/", views.college_dashboard, name="college_dashboard"),
    path("logout/", views.user_logout, name="logout"),
    path("colleges/register/", views.register_college, name="register_college"),
    path("staff/college/<int:college_id>/manage/", views.manage_college, name="manage_college"),
    path("staff/college/<int:college_id>/api-key/", views.reset_api_key, name="reset_api_key"),

]

