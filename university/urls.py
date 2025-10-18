from django.urls import path
from . import views

app_name = "university"

urlpatterns = [
    path("dashboard/<int:university_id>", views.university_dashboard, name="university_dashboard"),
    path("register/", views.register_university, name="register_university"),
]

