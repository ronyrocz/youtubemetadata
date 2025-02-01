import pytest

from django.urls import reverse
from rest_framework import status

from videoservice import settings
from videoservice.models.channel import Channel
from videoservice.models.video import Video
from datetime import datetime


@pytest.mark.django_db
class TestVideoView:
    def setup_method(self, method):
        settings.USE_REDIS = False
        settings.USE_CELERY = False

    def test_get_videos_success(self, client):
        """Test GET /videos with a valid channel_id returning 5 videos."""
        # Create a channel
        channel = Channel.objects.create(channel_id="UC123456", name="Test Channel")

        # Create 5 videos
        for i in range(5):
            Video.objects.create(
                video_id=f"vid{i}",
                video_title=f"Video {i}",
                upload_date=datetime(2024, 3, 1),
                channel=channel,
            )

        url = reverse("video-list") + "?channel_id=UC123456"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["UC123456"]) == 5  # Ensure 5 videos returned

    def test_get_videos_no_channel(self, client):
        """Test GET /videos when channel does not exist (should call Mock YouTube API)."""
        url = reverse("video-list") + "?channel_id=NON_EXISTENT_CHANNEL"
        response = client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert (
            response.json()
            == {
                "errors": [
                    {
                        "detail": "Channel ID not found or no videos available.",
                        "source": {"parameter": "detail"},
                        "status": "404",
                        "title": "Not Found",
                    }
                ]
            }
            != {"error": "Channel ID not found in mock YouTube API"}
        )

    def test_get_videos_no_channel_id(self, client):
        """Test GET /videos without channel_id query param (should return 400)."""
        url = reverse("video-list")
        response = client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.json()
            == {
                "errors": [
                    {
                        "detail": "This field is required.",
                        "source": {"parameter": "channel_id"},
                        "status": "400",
                        "title": "Bad Request",
                    }
                ]
            }
            != {"error": "channel_id is required"}
        )

    def test_post_videos_not_allowed(self, client):
        """Test POST /videos should return 405 Method Not Allowed."""
        url = reverse("video-list")
        response = client.post(url, {})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_put_videos_not_allowed(self, client):
        """Test PUT /videos should return 405 Method Not Allowed."""
        url = reverse("video-list")
        response = client.put(url, {})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_videos_not_allowed(self, client):
        """Test DELETE /videos should return 405 Method Not Allowed."""
        url = reverse("video-list")
        response = client.delete(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


