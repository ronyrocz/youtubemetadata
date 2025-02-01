
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from celery import shared_task
from django.core.cache import cache
from django.db import transaction
from videoservice import settings
from videoservice.models.channel import Channel
from videoservice.models.video import Video

logger = logging.getLogger("videoservice")
CACHE_LIMIT = 5
THREAD_POOL = ThreadPoolExecutor(max_workers=5)

try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

def async_store_videos_in_db(channel_id, videos_data):
    """
    Store videos asynchronously, using Celery if available, otherwise use ThreadPoolExecutor.
    """
    if CELERY_AVAILABLE and getattr(settings, "USE_CELERY", True):
        logger.info(f"Using Celery for async task: Storing videos for {channel_id}")
        store_videos_in_db.delay(channel_id, videos_data)
    else:
        logger.info(f"Using ThreadPoolExecutor (fallback) for async task: Storing videos for {channel_id}")
        THREAD_POOL.submit(store_videos_in_db_sync, channel_id, videos_data)

@shared_task
def store_videos_in_db(channel_id, videos_data):
    """Asynchronously store fetched videos in the database (Celery)."""
    logger.info(f"Celery Task: Storing videos for channel {channel_id}")
    store_videos_in_db_sync(channel_id, videos_data)

def store_videos_in_db_sync(channel_id, videos_data):
    """Synchronous DB storage (used by Celery & ThreadPoolExecutor)."""
    try:
        # Ensure the channel exists
        channel, _ = Channel.objects.get_or_create(
            channel_id=channel_id, defaults={"name": f"Mock Channel {channel_id}"}
        )

        # Prepare video objects for bulk insert
        video_objects = [
            Video(
                video_id=video["video_id"],
                video_title=video["video_title"],
                upload_date=datetime.strptime(video["upload_date"], "%Y-%m-%d"),
                channel=channel,
            )
            for video in videos_data
        ]

        # Bulk insert videos into DB (ignore conflicts)
        with transaction.atomic():
            Video.objects.bulk_create(video_objects, ignore_conflicts=True)

        logger.info(f"Successfully stored {len(video_objects)} videos for channel {channel_id}")
    except Exception as e:
        logger.error(f"Failed to store videos for {channel_id}: {str(e)}")


def async_update_last_accessed(channel_id):
    """
    Updates last_accessed field asynchronously.
    Uses Celery if available; otherwise, falls back to ThreadPoolExecutor.
    """
    if CELERY_AVAILABLE and getattr(settings, "USE_CELERY", True):
        logger.info(f"Using Celery for async task: Updating last_accessed for {channel_id}")
        update_last_accessed.delay(channel_id)  # ✅ Celery Async Task
    else:
        logger.info(f"Using ThreadPoolExecutor (fallback) for async task: Updating last_accessed for {channel_id}")
        THREAD_POOL.submit(update_last_accessed_sync, channel_id)  # ✅ ThreadPoolExecutor Fallback

@shared_task
def update_last_accessed(channel_id):
    """Celery task to update last_accessed timestamp."""
    logger.info(f"🚀 Celery Task Running: Updating last_accessed for {channel_id}")
    update_last_accessed_sync(channel_id)

def update_last_accessed_sync(channel_id):
    """Synchronous function to update last_accessed (used by Celery & Threading)."""
    try:
        Channel.objects.filter(channel_id=channel_id).update(last_accessed=datetime.now())
        logger.info(f"✅ last_accessed updated for {channel_id}")
    except Exception as e:
        logger.error(f"❌ Failed to update last_accessed for {channel_id}: {str(e)}")


## TODO Future implementation to implement cache update with LRU strategy
@shared_task
def update_video_cache():
    """Background task to refresh Redis cache for the most active channels."""
    logger.info("🚀 Running periodic video cache refresh...")

    # ✅ Fetch only the most recently accessed channels
    active_channels = Channel.objects.order_by("-last_accessed")[:CACHE_LIMIT]

    for channel in active_channels:
        # Get latest 5 videos
        videos = list(Video.objects.filter(channel=channel).order_by("-upload_date")[:5])

        if videos:
            video_ids = [video.video_id for video in videos]
            cache_key = f"recent_videos:{channel.channel_id}"

            # ✅ Store video IDs in Redis with TTL
            cache.set(cache_key, video_ids, timeout=300)

    logger.info(f"✅ Updated Redis cache for {len(active_channels)} active channels.")

    return "Cache Updated"