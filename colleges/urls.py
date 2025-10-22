from django.urls import path
from . import views

app_name = "colleges"

urlpatterns = [
    path("dashboard/", views.college_dashboard, name="college_dashboard"),
    path("register/", views.register_college, name="register_college"),
    path("<int:college_id>/", views.manage_college, name="manage_college"),
    path("<int:college_id>/api-key/", views.reset_api_key, name="reset_api_key"),
    path("<int:college_id>/register-user/", views.register_college_user, name="register_college_user"),
    path("create-password/<uuid:uuid>/", views.create_college_user_password, name="create_college_user_password"),
    path("<int:college_id>/edit-user/<int:user_id>/", views.edit_college_user, name="edit_college_user"),
    path("<int:college_id>/delete-user/<int:user_id>/", views.delete_college_user, name="delete_college_user"),
    path("trigger-password-reset/<int:user_id>/", views.trigger_password_reset, name="trigger_password_reset"),
]
