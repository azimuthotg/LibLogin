from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    get_background_image,
    get_slide_content,
    BackgroundImageViewSet,
    SystemSettingsViewSet,
    UserViewSet
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'backgrounds', BackgroundImageViewSet, basename='background')
router.register(r'settings', SystemSettingsViewSet, basename='settings')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # Public endpoint for MikroTik to fetch background image
    path('login-background/', get_background_image, name='login-background'),

    # Public endpoint for MikroTik to fetch slide content
    path('slide-content/', get_slide_content, name='slide-content'),

    # Include router URLs
    path('', include(router.urls)),
]
