from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    get_background_image,
    get_slide_content,
    get_template_config,
    get_hotspot_choices,
    track_impression,
    BackgroundImageViewSet,
    SystemSettingsViewSet,
    UserViewSet,
    HotspotViewSet
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'backgrounds', BackgroundImageViewSet, basename='background')
router.register(r'settings', SystemSettingsViewSet, basename='settings')
router.register(r'users', UserViewSet, basename='user')
router.register(r'hotspots', HotspotViewSet, basename='hotspot')

urlpatterns = [
    # Public endpoint for MikroTik to fetch background image
    path('login-background/', get_background_image, name='login-background'),

    # Public endpoint for MikroTik to fetch slide content
    path('slide-content/', get_slide_content, name='slide-content'),

    # Public endpoint for MikroTik to fetch complete template configuration
    path('template-config/', get_template_config, name='template-config'),

    # Hotspot choices for dropdowns
    path('hotspot-choices/', get_hotspot_choices, name='hotspot-choices'),

    # Page impression tracking (public endpoint for MikroTik login pages)
    path('track-impression/', track_impression, name='track-impression'),

    # Include router URLs
    path('', include(router.urls)),
]
