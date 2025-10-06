import os
from django.utils import timezone
from django.db import models
from colleges.models import College

def backup_upload_path(instance, filename):
    timestamp = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join("backups", instance.college.code, f"{timestamp}_{filename}")

class Backup(models.Model):
    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name="backups"
    )
    file = models.FileField(upload_to=backup_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    checksum = models.CharField(max_length=64, blank=True, null=True, help_text="SHA256 checksum")
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.college.code} - {self.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')}"
