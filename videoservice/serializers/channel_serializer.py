from rest_framework import serializers

from videoservice.models.channel import Channel

class ChannelSerializer(serializers.ModelSerializer):
    """
    Serializer for the Channel model.

    Serializes all fields of the Channel model for API responses.
    """
    class Meta:
        model = Channel
        fields = '__all__'