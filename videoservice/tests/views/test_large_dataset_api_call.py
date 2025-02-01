import pytest
import random
from django.urls import reverse
from rest_framework import status

from videoservice import settings
from videoservice.models.channel import Channel
from videoservice.models.video import Video
from datetime import datetime

@pytest.mark.django_db
class TestLargeDatasetAPI:

    def setup_method(self):
        """Setup method to create multiple channels and videos."""
        self.channels = []
        settings.USE_REDIS = False
        settings.USE_CELERY = False

        # ✅ Create 10 channels
        for i in range(10):
            channel = Channel.objects.create(
                channel_id=f"UC_TEST_{i}",
                name=f"Test Channel {i}"
            )
            self.channels.append(channel)

            # ✅ Create 5+ videos per channel
            for j in range(5):
                Video.objects.create(
                    video_id=f"vid_{i}_{j}",
                    video_title=f"Test Video {j} for Channel {i}",
                    upload_date=datetime(2024, 3, 1, 12, j),  # ✅ Unique timestamps
                    channel=channel
                )

    def test_large_dataset_random_channel_api_calls(self, client):
        """Test making API calls for 10 random channels and assert response correctness."""
        for _ in range(10):  # ✅ Perform 10 random calls
            random_channel = random.choice(self.channels)

            url = reverse("video-list") + f"?channel_id={random_channel.channel_id}"
            response = client.get(url)

            assert response.status_code == status.HTTP_200_OK, f"Failed for {random_channel.channel_id}"
            assert len(response.json()[random_channel.channel_id]) == 5, f"Incorrect response length for {random_channel.channel_id}"