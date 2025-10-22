from django.urls import path
from . import views

app_name = "colleges"

urlpatterns = [
    path("dashboard/", views.college_dashboard, name="college_dashboard"),
    path("register/", views.register_college, name="register_college"),
    path("<int:college_id>/", views.manage_college, name="manage_college"),
    path("<int:college_id>/api-key/", views.reset_api_key, name="reset_api_key"),

]
