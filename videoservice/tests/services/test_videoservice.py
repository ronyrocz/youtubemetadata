import json
from unittest.mock import patch, MagicMock

import pytest
from rest_framework.exceptions import ValidationError, NotFound

from videoservice.models.channel import Channel
from videoservice.models.video import Video
from videoservice.services.video_service import VideoService


@pytest.mark.django_db
class TestVideoService:

    def setup_method(self):
        """Setup before each test case."""
        self.channel = Channel.objects.create(channel_id="UC123456", name="Test Channel")

        self.videos_data = [
            {"video_id": f"vid{i}", "video_title": f"Video {i}", "upload_date": "2024-03-01"}
            for i in range(5)
        ]

        self.video_objects = [
            Video.objects.create(
                video_id=video["video_id"],
                video_title=video["video_title"],
                upload_date="2024-03-01",
                channel=self.channel
            )
            for video in self.videos_data
        ]

    @patch("videoservice.services.video_service.cache.get", return_value=["vid0", "vid1", "vid2", "vid3", "vid4"])
    @patch("videoservice.services.video_service.cache.set")
    @patch("videoservice.models.video.Video.objects.filter")  # ✅ Mock DB query correctly
    @patch("videoservice.services.video_service.async_update_last_accessed")  # ✅ Mock Celery Task
    @patch("videoservice.services.video_service.async_store_videos_in_db")  # ✅ Mock Celery Task
    def test_get_recent_videos_cache_hit(
            self, mock_store_task, mock_update_task, mock_filter, mock_cache_set, mock_cache_get
    ):
        """Test retrieving videos from cache (mocked)."""

        # ✅ Mock the QuerySet so `.order_by()` does not fail
        mock_filter.return_value.order_by.return_value = self.video_objects

        response, status_code = VideoService.get_recent_videos(self.channel.channel_id)

        assert status_code == 200
        assert len(response) == 5  # ✅ Cache returned correct data
        mock_filter.assert_called_once()  # ✅ Ensure DB query is still happening
        mock_cache_get.assert_called_once_with(f"recent_videos:{self.channel.channel_id}")
        mock_cache_set.assert_not_called()  # ✅ No cache update needed on cache hit

    @patch("videoservice.services.video_service.cache.get", return_value=None)  # ✅ Simulate cache miss
    @patch("videoservice.services.video_service.cache.set")  # ✅ Mock cache set
    @patch("videoservice.services.video_service.async_update_last_accessed")  # ✅ Mock Celery Task
    @patch("videoservice.services.video_service.async_store_videos_in_db")
    def test_get_recent_videos_cache_miss_fetch_from_db(self,mock_store_task, mock_update_task, mock_cache_set, mock_cache_get):
        """Test fetching videos from database when cache is empty."""
        response, status_code = VideoService.get_recent_videos(self.channel.channel_id)

        assert status_code == 200
        assert len(response) == 5  # ✅ Ensure 5 videos are fetched from DB
        mock_cache_get.assert_called_once()
        mock_cache_set.assert_called_once()  # ✅ Ensure cache is updated after DB fetch

    @patch("videoservice.services.video_service.cache.get", return_value=None)  # ✅ Simulate cache miss
    @patch("videoservice.services.video_service.cache.set")  # ✅ Mock cache set
    @patch("videoservice.services.video_service.VideoService.fetch_and_store_videos")
    @patch("videoservice.services.video_service.async_update_last_accessed")  # ✅ Mock Celery Task
    @patch("videoservice.services.video_service.async_store_videos_in_db")
    def test_get_recent_videos_cache_miss_fetch_from_api(self,mock_store_task, mock_update_task, mock_fetch_api,mock_cache_set, mock_cache_get):
        """Test fallback to API when cache and DB are empty."""
        mock_fetch_api.return_value = self.videos_data  # ✅ Mock API response

        Channel.objects.filter(channel_id=self.channel.channel_id).delete()  # ✅ Remove DB records

        response, status_code = VideoService.get_recent_videos(self.channel.channel_id)

        assert status_code == 200
        assert len(response) == 5  # ✅ Ensure 5 videos are returned from API
        mock_fetch_api.assert_called_once_with(self.channel.channel_id)  # ✅ Ensure API was called

    @patch("videoservice.services.video_service.cache.get", return_value=None)
    def test_get_recent_videos_invalid_channel_id(self, mock_cache_get):
        """Test validation error when channel_id is missing."""
        with pytest.raises(ValidationError):
            VideoService.get_recent_videos(None)

    @patch("videoservice.services.video_service.cache.get", return_value=None)
    def test_get_recent_videos_not_found(self, mock_cache_get):
        """Test error handling when channel ID is not found in DB and API."""
        Channel.objects.filter(channel_id=self.channel.channel_id).delete()

        with patch("videoservice.services.video_service.VideoService.fetch_videos_from_mock_youtube") as mock_fetch_api:
            mock_fetch_api.return_value = []  # ✅ Mock empty API response
            with pytest.raises(NotFound):
                VideoService.get_recent_videos(self.channel.channel_id)

    @patch("videoservice.services.video_service.VideoService.fetch_videos_from_mock_youtube")
    @patch("videoservice.services.video_service.async_update_last_accessed")  # ✅ Mock Celery Task
    @patch("videoservice.services.video_service.async_store_videos_in_db")
    def test_fetch_and_store_videos_from_mock_api(self,mock_store_task, mock_update_task, mock_fetch_api):
        """Test fetching from mock YouTube API and storing in DB."""
        mock_fetch_api.return_value = self.videos_data  # ✅ Mock API response

        response = VideoService.fetch_and_store_videos(self.channel.channel_id)

        assert len(response) == 5  # ✅ Ensure 5 videos are fetched from API
        mock_fetch_api.assert_called_once_with(self.channel.channel_id)

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_fetch_videos_from_mock_youtube_not_found(self, mock_open):
        """Test when channel is not found in mock YouTube API."""
        response = VideoService.fetch_videos_from_mock_youtube("NON_EXISTENT_CHANNEL")
        assert response == []  # ✅ Ensure empty response on file not found

    @patch("builtins.open", new_callable=MagicMock)
    def test_fetch_videos_from_mock_youtube_success(self, mock_open):
        """Test reading from mock YouTube JSON file."""

        mock_json_data = json.dumps({"UC123456": self.videos_data})  # ✅ Proper JSON string

        # ✅ Ensure `.read()` returns a **string** instead of a `MagicMock`
        mock_open.return_value.__enter__.return_value.read.return_value = mock_json_data

        response = VideoService.fetch_videos_from_mock_youtube("UC123456")

        assert len(response) == 5  # ✅ Ensure correct number of videos
