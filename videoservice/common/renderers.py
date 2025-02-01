from rest_framework.renderers import JSONRenderer

class VideoJSONRenderer(JSONRenderer):
    """
    Custom renderer to format video response data.
    This ensures API responses follow the format:
    {
      "channel_id": [
        { "video_id": "...", "video_title": "...", "upload_date": "..." }
      ]
    }
    The renderer modifies DRF’s default response structure by grouping videos under their respective `channel_id`.
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Modify the response structure to group videos under `channel_id`.
        """
        request = renderer_context.get('request', None)

        # Ensure we have a valid request object and "channel_id" param is present
        if request and request.query_params.get("channel_id"):
            channel_id = request.query_params["channel_id"]

            # If the response data is a list (default DRF serializer format), transform it
            if isinstance(data, list):
                data = {channel_id: data}

        return super().render(data, accepted_media_type, renderer_context)
