from django.urls import path
from .views import BackupUploadAPIView, backup_list, download_backup, college_backup_list

app_name = "backups"

urlpatterns = [
    path('upload/', BackupUploadAPIView.as_view(), name='backup-upload'),
    path("", backup_list, name="backup_list"),
    path("download/<int:backup_id>/", download_backup, name="download_backup"),
    path("colleges/<int:college_id>/", college_backup_list, name="college_backup_list"),

]
