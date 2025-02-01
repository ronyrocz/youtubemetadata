from rest_framework.routers import DefaultRouter
from django.urls import path, include
from videoservice.views.video_view import VideoView

router = DefaultRouter()
router.register(r'video', VideoView, basename='video')
urlpatterns = [
    path("", include(router.urls)),
]
