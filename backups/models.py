import os
import hashlib
from django.db import models
from django.utils import timezone
from django.core.files.storage import default_storage
from colleges.models import College
from .utils.encryption import encrypt_file

def temp_backup_upload_path(instance, filename):
    return os.path.join("backups", "temp", filename)


class Backup(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name="backups")
    file = models.FileField(upload_to=temp_backup_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    checksum = models.CharField(max_length=64, blank=True, null=True, help_text="SHA256 checksum")
    remarks = models.TextField(blank=True, null=True)
    is_encrypted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-uploaded_at"]

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if self.file and not self.file_size:
            self.file_size = self.file.size

        if self.file and not self.checksum:
            sha256 = hashlib.sha256()
            for chunk in self.file.chunks():
                sha256.update(chunk)
            self.checksum = sha256.hexdigest()

        super().save(*args, **kwargs)

        # Move and encrypt only after file is saved and college assigned
        if is_new and self.college_id and "temp" in self.file.name:
            timestamp = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.basename(self.file.name)
            new_path = os.path.join("backups", self.college.code, f"{timestamp}_{filename}")
            old_path = self.file.name

            file_content = self.file
            default_storage.save(new_path, file_content)
            default_storage.delete(old_path)

            self.file.name = new_path
            super().save(update_fields=["file"])

            # Encrypt in place (add .enc suffix)
            try:
                encrypted_path = encrypt_file(self.file.path)
                os.remove(self.file.path)
                self.file.name = f"{self.file.name}.enc"
                self.is_encrypted = True
                super().save(update_fields=["file", "is_encrypted"])
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Encryption failed for backup {self.id}: {e}")

    def __str__(self):
        return (
            f"{self.college.code} - {self.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')}"
            if self.college_id else f"Unassigned Backup ({self.uploaded_at})"
        )
