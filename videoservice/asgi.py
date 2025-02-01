"""
ASGI config for videoservice project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "videoservice.settings")
django.setup()

from django.db.utils import OperationalError, ProgrammingError
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'videoservice.settings')

application = get_asgi_application()

logger = logging.getLogger(__name__)

def create_periodic_task():
    """Ensures the Celery Beat periodic task for cache refresh is created on startup."""
    logger.info("Ensuring Celery Beat periodic task exists...")

    try:
        # ✅ Create interval schedule (every 5 minutes)
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=5,
            period=IntervalSchedule.MINUTES,
        )

        # ✅ Ensure the periodic task exists (avoid duplicates)
        task_name = "videoservice.tasks.update_video_cache"  # ✅ Match the actual function name
        if not PeriodicTask.objects.filter(task=task_name).exists():
            PeriodicTask.objects.create(
                interval=schedule,
                name="Refresh Video Cache",  # ✅ Display name (human-readable)
                task=task_name,  # ✅ Celery function path
                args=json.dumps([]),  # ✅ No arguments needed for periodic updates
            )
            logger.info(f"Created Celery Beat periodic task: {task_name}")
        else:
            logger.info(f"Celery Beat periodic task {task_name} already exists.")

    except (OperationalError, ProgrammingError):
        # 🔥 Handle cases where DB isn't ready yet (happens on fresh migrations)
        logger.warning("Database is not ready. Skipping Celery Beat setup for now.")

# ✅ Run this function at startup
create_periodic_task()
