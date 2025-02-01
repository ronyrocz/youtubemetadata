from django.db import models

class Channel(models.Model):
    """
    Model representing a YouTube channel.

    Attributes:
        channel_id (str): Unique identifier for the channel (Primary Key).
        name (str, optional): The name of the channel (nullable).
        created_at (datetime): Timestamp indicating when the channel was created.
        last_accessed (datetime): Timestamp indicating the last time the channel was accessed.
    """
    channel_id = models.CharField(max_length=255, unique=True, primary_key=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.channel_id
