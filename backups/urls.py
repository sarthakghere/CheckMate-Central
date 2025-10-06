from django.urls import path
from .views import BackupUploadAPIView

urlpatterns = [
    path('upload/', BackupUploadAPIView.as_view(), name='backup-upload'),
]
