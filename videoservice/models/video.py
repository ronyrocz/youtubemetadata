from django.db import models

from videoservice.models.channel import Channel

class Video(models.Model):
    """
    Model representing a YouTube video stored in the system.

    Attributes:
        video_id (str): Unique identifier for the video.
        video_title (str): The title of the video.
        upload_date (datetime): Timestamp indicating when the video was uploaded.
        channel (ForeignKey): Foreign key linking the video to its respective channel.
    """
    video_id = models.CharField(max_length=255, primary_key=True)
    video_title = models.CharField(max_length=255)
    upload_date = models.DateTimeField()
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="videos")

    class Meta:
        ordering = ['-upload_date']

    def __str__(self):
        return self.video_title
