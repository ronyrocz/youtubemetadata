from rest_framework.views import exception_handler
from rest_framework.response import Response
import logging
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Custom exception handler to follow JSON:API spec."""
    response = exception_handler(exc, context)

    if response is not None:
        # Transform the error response to JSON:API error format
        if isinstance(response.data, dict):
            errors = [
                {
                    "status": str(response.status_code),
                    "title": response.status_text,
                    "source": {"parameter": key},
                    "detail": value[0] if isinstance(value, list) else value,
                }
                for key, value in response.data.items()
            ]
        else:
            errors = [
                {"status": str(response.status_code), "title": response.status_text, "detail": str(response.data)}]

        return Response({"errors": errors}, status=response.status_code)

    # Handle unexpected exceptions (500 errors)
    logger.error(f"Unhandled exception in {context['view']}: {exc}")
    return Response(
        {
            "errors": [
                {
                    "status": "500",
                    "title": "Internal Server Error",
                    "detail": "An unexpected error occurred.",
                }
            ]
        },
        status=500
    )


class CustomValidationError(APIException):
    status_code = 400
    default_detail = "A validation error occurred."

    def __init__(self, detail):
        if isinstance(detail, dict):
            self.detail = detail
        else:
            self.detail = {"error": detail}

