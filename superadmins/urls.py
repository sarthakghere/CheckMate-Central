from django.urls import path
from . import views

app_name = "superadmin"

urlpatterns = [
    path("login/", views.email_password_login, name="login"),
    path("otp-verify/", views.otp_verify, name="otp_verify"),
    # path("dashboard/", views.dashboard, name="dashboard"),
    # path("logout/", views.centraladmin_logout, name="logout"),
]
