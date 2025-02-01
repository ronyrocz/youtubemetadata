import json
import logging
import os
from datetime import datetime

from rest_framework.exceptions import ValidationError, NotFound

from videoservice import settings
from videoservice.models.channel import Channel
from videoservice.models.video import Video
from videoservice.config.tasks import update_last_accessed, store_videos_in_db, async_store_videos_in_db, \
    async_update_last_accessed
from videoservice.serializers.video_serializer import VideoSerializer
from django.core.cache import cache

logger = logging.getLogger('videoservice')


class VideoService:
    """
    Service layer for handling video-related operations, including:
    - Fetching recent videos from the database or an external API.
    - Caching video results for performance optimization.
    - Storing newly fetched videos in the database asynchronously.
    """

    CACHE_EXPIRY = 300  # Cache TTL = 5 minutes

    @classmethod
    def get_recent_videos(cls, channel_id):
        """
        Fetches the most recent 5 videos for a given channel ID.
        - If cached, retrieves from Redis.
        - Otherwise, fetches from the database or external API.
        Args:
            channel_id (str): The unique identifier of the YouTube channel.
        Returns:
            tuple: (list of serialized video data, HTTP status code)
        """
        logger.info(f"Fetching recent videos for channel: {channel_id}")

        if not channel_id:
            raise ValidationError({"channel_id": ["This field is required."]})

        redis_key = f"recent_videos:{channel_id}"

        video_ids  = cache.get(redis_key) if settings.USE_REDIS else None
        if video_ids:
            logger.debug(f"Cache hit for channel {channel_id}, fetching from database")
            videos = list(Video.objects.filter(video_id__in=video_ids).order_by("-upload_date"))
            if not videos and len(videos) != 5:
                logger.info(f"Cache had less than 5 videos for channel {channel_id}, fetching from API")
                videos  = cls.fetch_and_cache_videos(channel_id)
        else:
            logger.info(f"Cache miss for channel {channel_id}, fetching from database/API")
            videos = cls.fetch_and_cache_videos(channel_id)

        serializer = VideoSerializer(videos, many=True)
        # Async update last_accessed in background (non-blocking)
        async_update_last_accessed(channel_id)
        return serializer.data, 200


    @classmethod
    def fetch_and_cache_videos(cls, channel_id):
        """
        Fetches the most recent 5 videos from the database or external API if not available.
        Args:
            channel_id (str): The unique identifier of the YouTube channel.
        Returns:
            list: Video objects retrieved from DB or API.
        """

        logger.info(f"Fetching videos for channel {channel_id} from database or external source")

        channel = Channel.objects.filter(channel_id=channel_id).first()
        videos = []
        if channel:
            # Fetch latest 5 videos from the database
            videos = list(Video.objects.filter(channel=channel).order_by("-upload_date")[:5])

        if not channel or not videos:
            logger.info(f"Channel {channel_id} not found in DB or has no videos, fetching from API")
            api_videos = cls.fetch_and_store_videos(channel_id)
            # Convert API response format into Django ORM objects before serializing
            videos = [
                Video(
                    video_id=video["video_id"],
                    video_title=video["video_title"],
                    upload_date=datetime.strptime(video["upload_date"], "%Y-%m-%d"),
                    channel=channel,
                )
                for video in api_videos
            ]

        if not videos:
            raise NotFound("Channel ID not found or no videos available.")

        video_ids = [video.video_id for video in videos]

        # Store video IDs in cache
        if settings.USE_REDIS:
            cache_key = f"recent_videos:{channel_id}"
            cache.set(cache_key, video_ids, timeout=cls.CACHE_EXPIRY)
        return videos

    @classmethod
    def fetch_and_store_videos(cls, channel_id):
        """
        Fetches videos from the Mock YouTube API and stores them asynchronously in the database.
        Args:
            channel_id (str): The unique identifier of the YouTube channel.
        Returns:
            list: Video data fetched from the external API.
        """

        logger.info(f"Fetching videos for channel {channel_id} from Mock YouTube API")
        mock_videos = cls.fetch_videos_from_mock_youtube(channel_id)

        if not mock_videos:
            logger.warning(f"No videos found in Mock YouTube API for channel {channel_id}")
            raise NotFound("Channel ID not found or no videos available.")

        # Store fetched videos in DB asynchronously using Celery
        async_store_videos_in_db(channel_id, mock_videos)

        return mock_videos

    @classmethod
    def fetch_videos_from_mock_youtube(cls, channel_id):
        """
        Reads video data from a mock JSON file, simulating the YouTube Data API.
        Args:
            channel_id (str): The unique identifier of the YouTube channel.
        Returns:
            list: A list of video dictionaries with video_id, title, and upload_date.
        """
        json_file_path = os.path.join(settings.BASE_DIR,"videoservice","fixtures", "api_take_home_JSON_file.json")
        try:
            with open(json_file_path, "r") as file:
                data = json.load(file)
        except FileNotFoundError:
            logger.error(f"Mock YouTube JSON file not found at {json_file_path}")
            return []

        videos = data.get(channel_id, [])

        if not videos:
            return []

        # Sort videos by upload_date (newest first) and return the top 5
        videos_sorted = sorted(videos, key=lambda x: x["upload_date"], reverse=True)

        return videos_sorted[:5]


