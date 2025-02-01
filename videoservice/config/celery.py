import os
from celery import Celery

# Set Django settings module (Make sure this points to your correct settings file)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "videoservice.settings")

celery_app = Celery("videoservice")

# Load Celery configuration from Django settings
celery_app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed Django apps
celery_app.autodiscover_tasks()
