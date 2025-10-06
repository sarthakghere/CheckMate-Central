import os
import hashlib
from django.db import models
from django.utils import timezone
from colleges.models import College

def temp_backup_upload_path(instance, filename):
    # Temporarily store before college is assigned
    return os.path.join("backups", "temp", filename)

class Backup(models.Model):
    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name="backups"
    )
    file = models.FileField(upload_to=temp_backup_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    checksum = models.CharField(max_length=64, blank=True, null=True, help_text="SHA256 checksum")
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def save(self, *args, **kwargs):
        # Assign file size & checksum if available
        if self.file and not self.file_size:
            self.file_size = self.file.size

        # Compute SHA256 checksum if not already set
        if self.file and not self.checksum:
            sha256 = hashlib.sha256()
            for chunk in self.file.chunks():
                sha256.update(chunk)
            self.checksum = sha256.hexdigest()

        super().save(*args, **kwargs)

        # Move file to the correct folder once college is known
        if self.college_id and "temp" in self.file.name:
            timestamp = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.basename(self.file.name)
            new_path = os.path.join("backups", self.college.code, f"{timestamp}_{filename}")
            from django.core.files.storage import default_storage

            # Move within storage
            old_path = self.file.name
            file_content = self.file
            default_storage.save(new_path, file_content)
            default_storage.delete(old_path)

            # Update path and re-save without recursion
            self.file.name = new_path
            super().save(update_fields=["file"])
    
    def __str__(self):
        if self.college_id:
            return f"{self.college.code} - {self.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')}"
        return f"Unassigned Backup ({self.uploaded_at})"
