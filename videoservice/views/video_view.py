import logging

from rest_framework import viewsets
from rest_framework.response import Response

from videoservice.common.exceptions import custom_exception_handler
from videoservice.models.video import Video
from videoservice.common.renderers import VideoJSONRenderer
from videoservice.serializers.video_serializer import VideoSerializer
from videoservice.services.video_service import VideoService

logger = logging.getLogger('videoservice')

class VideoView(viewsets.ReadOnlyModelViewSet):
    """
    API view for retrieving the most recent videos for a given channel.
    This view only supports `GET` requests and formats responses using a custom JSON renderer.
    """
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    renderer_classes = [VideoJSONRenderer]

    def get_exception_handler(self):
        """
        Returns a custom exception handler for API errors.
        Returns:
            function: Custom exception handler for structured API responses.
        """
        return custom_exception_handler

    def list(self, request):
        """
        Handles GET requests to retrieve the most recent videos for a given channel.
        Args:
            request (Request): The HTTP request object.
        Returns:
            Response: A JSON response containing the latest 5 videos or an error message.
        """
        logger.info("LIST API called")
        channel_id = request.query_params.get("channel_id")
        response_data, status_code = VideoService.get_recent_videos(channel_id=channel_id)
        return Response(response_data, status=status_code)