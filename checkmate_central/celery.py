# myproject/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'checkmate_central.settings')

app = Celery('checkmate_central')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
