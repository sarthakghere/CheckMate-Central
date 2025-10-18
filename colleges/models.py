from django.db import models
from rest_framework_api_key.models import APIKey

class College(models.Model):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=50, unique=True)
    university = models.ForeignKey(
        'university.University',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='colleges'
    )
    
    api_key = models.OneToOneField(
        APIKey,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="college"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
