from rest_framework import serializers
from .models import Backup
import hashlib

class BackupUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Backup
        fields = ['file', 'remarks']

    def create(self, validated_data):
        # Compute checksum
        file_obj = validated_data['file']
        file_obj.seek(0)
        sha256 = hashlib.sha256()
        for chunk in file_obj.chunks():
            sha256.update(chunk)
        validated_data['checksum'] = sha256.hexdigest()
        validated_data['file_size'] = file_obj.size
        return super().create(validated_data)
