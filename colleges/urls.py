from django.urls import path
from . import views

app_name = "colleges"

urlpatterns = [
    path("dashboard/college/", views.college_dashboard, name="college_dashboard"),
    path("colleges/register/", views.register_college, name="register_college"),
    path("staff/college/<int:college_id>/manage/", views.manage_college, name="manage_college"),
    path("staff/college/<int:college_id>/api-key/", views.reset_api_key, name="reset_api_key"),
]
