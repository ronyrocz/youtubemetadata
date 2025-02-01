from rest_framework import serializers

from videoservice.models.video import Video

class VideoSerializer(serializers.ModelSerializer):
    """
    Serializer for the Video model.

    Serializes all fields of the Video model for API responses.
    """
    class Meta:
        model = Video
        fields = '__all__'
