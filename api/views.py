from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from .models import BackgroundImage, SystemSettings, SlideContent, TemplateConfig, CardContent, Hotspot, PageImpression, DailyReachStats, LandingPageURL
from .serializers import (
    BackgroundImageSerializer,
    BackgroundImageUploadSerializer,
    SystemSettingsSerializer,
    UserSerializer,
    TemplateConfigSerializer,
    TemplateConfigFullSerializer,
    SlideContentSerializer,
    CardContentSerializer,
    HotspotSerializer,
    HotspotChoiceSerializer,
    LandingPageURLSerializer
)
import logging
import hashlib
from django.utils import timezone
from datetime import date, timedelta
from django.db.models import Count, Avg, Sum, Q
from django.db.models.functions import TruncDate, TruncHour
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import os
from django.conf import settings as django_settings

# Configure logging
logger = logging.getLogger(__name__)


# Register Thai fonts for PDF generation
def register_thai_fonts():
    """Register Thai fonts (TH Sarabun New) for ReportLab"""
    try:
        # Get base directory
        base_dir = django_settings.BASE_DIR
        fonts_dir = os.path.join(base_dir, 'fonts')

        # Register TH Sarabun New fonts
        pdfmetrics.registerFont(TTFont('THSarabun', os.path.join(fonts_dir, 'THSarabunNew.ttf')))
        pdfmetrics.registerFont(TTFont('THSarabun-Bold', os.path.join(fonts_dir, 'THSarabunNew Bold.ttf')))
        pdfmetrics.registerFont(TTFont('THSarabun-Italic', os.path.join(fonts_dir, 'THSarabunNew Italic.ttf')))
        pdfmetrics.registerFont(TTFont('THSarabun-BoldItalic', os.path.join(fonts_dir, 'THSarabunNew BoldItalic.ttf')))

        logger.info("[PDF] Thai fonts registered successfully")
        return True
    except Exception as e:
        logger.warning(f"[PDF] Could not register Thai fonts: {str(e)}")
        return False


@api_view(['GET'])
@permission_classes([AllowAny])
def get_background_image(request):
    """
    Public API endpoint to get the current active background image
    Supports hotspot_name parameter for hotspot-specific backgrounds
    """
    hotspot_name = request.GET.get('hotspot_name', None)

    try:
        logger.info(f"[API] get_background_image called with hotspot_name={hotspot_name}")

        # Validate hotspot_name if provided
        if hotspot_name and len(hotspot_name) > 100:
            logger.warning(f"[API] Invalid hotspot_name length: {len(hotspot_name)}")
            return Response({
                'success': False,
                'message': 'Invalid hotspot_name parameter'
            }, status=status.HTTP_400_BAD_REQUEST)

        background = None

        # Try to get active background for specific hotspot
        if hotspot_name:
            background = BackgroundImage.objects.filter(
                hotspot_name=hotspot_name,
                is_active=True
            ).first()

            if background:
                logger.info(f"[API] Found hotspot-specific background: {background.title}")

        # Fallback to default background (no hotspot_name)
        if not background:
            background = BackgroundImage.objects.filter(
                hotspot_name__isnull=True,
                is_active=True
            ).first()

            if background:
                logger.info(f"[API] Using default background: {background.title}")

        if background:
            serializer = BackgroundImageSerializer(background, context={'request': request})
            return Response({
                'success': True,
                'imageUrl': serializer.data['image_url'],
                'title': serializer.data['title']
            })
        else:
            logger.warning("[API] No active background image found")
            return Response({
                'success': False,
                'message': 'No active background image found'
            }, status=status.HTTP_404_NOT_FOUND)

    except ValidationError as e:
        logger.error(f"[API] Validation error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Invalid request parameters'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"[API] Unexpected error in get_background_image: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': 'Internal server error. Please try again later.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BackgroundImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing background images
    Requires authentication
    """
    queryset = BackgroundImage.objects.all()
    serializer_class = BackgroundImageSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BackgroundImageUploadSerializer
        return BackgroundImageSerializer

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    @action(detail=True, methods=['post'])
    def set_active(self, request, pk=None):
        """Set this image as active"""
        image = self.get_object()
        image.is_active = True
        image.save()
        return Response({
            'success': True,
            'message': 'Background image set as active'
        })

    @action(detail=False, methods=['get'])
    def by_router(self, request):
        """Get images filtered by hotspot_name"""
        hotspot_name = request.query_params.get('hotspot_name', None)
        if hotspot_name:
            images = self.queryset.filter(hotspot_name=hotspot_name)
        else:
            images = self.queryset.filter(hotspot_name__isnull=True)

        serializer = self.get_serializer(images, many=True)
        return Response(serializer.data)


class SystemSettingsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing system settings
    Only admins can modify
    """
    queryset = SystemSettings.objects.all()
    serializer_class = SystemSettingsSerializer
    permission_classes = [IsAdminUser]

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing users
    Only admins can access
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


@api_view(['GET'])
@permission_classes([AllowAny])
def get_slide_content(request):
    """
    Public API endpoint to get slide show content
    Supports hotspot_name parameter for device-specific slides
    Returns all active slides ordered by 'order' field
    """
    hotspot_name = request.GET.get('hotspot_name', None)

    try:
        # Get active slides for specific hotspot
        if hotspot_name:
            slides = SlideContent.objects.filter(
                hotspot_name=hotspot_name,
                is_active=True
            )
        else:
            # Get default slides (no hotspot_name)
            slides = SlideContent.objects.filter(
                hotspot_name__isnull=True,
                is_active=True
            )

        # If no hotspot-specific slides found, try default slides
        if hotspot_name and not slides.exists():
            slides = SlideContent.objects.filter(
                hotspot_name__isnull=True,
                is_active=True
            )

        if slides.exists():
            slide_data = []
            for slide in slides:
                slide_data.append({
                    'icon': slide.icon,
                    'title': slide.title,
                    'description': slide.description
                })

            return Response({
                'success': True,
                'slides': slide_data,
                'count': len(slide_data)
            })
        else:
            return Response({
                'success': False,
                'message': 'No active slides found',
                'slides': []
            }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            'success': False,
            'message': str(e),
            'slides': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_template_config(request):
    """
    Public API endpoint to get complete template configuration
    Returns template type, slides, cards, and background based on hotspot_name or template_id

    Parameters:
    - template_id: Specific template ID for preview (optional)
    - hotspot_name: Hotspot name for hotspot-specific templates (optional)

    Response format:
    {
        "success": true,
        "template_name": "...",
        "left_panel_component": "slideshow" | "fullbg" | "cardgallery",
        "slides": [...],  // if component is slideshow
        "cards": [...],   // if component is cardgallery
        "background": {...}
    }
    """
    hotspot_name = request.GET.get('hotspot_name', None)
    template_id = request.GET.get('template_id', None)

    try:
        logger.info(f"[API] get_template_config called with hotspot_name={hotspot_name}, template_id={template_id}")

        # Validate hotspot_name if provided
        if hotspot_name and len(hotspot_name) > 100:
            logger.warning(f"[API] Invalid hotspot_name length: {len(hotspot_name)}")
            return Response({
                'success': False,
                'message': 'Invalid hotspot_name parameter'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get template config
        template_config = None

        # Priority 1: Specific template_id (for preview)
        if template_id:
            try:
                template_config = TemplateConfig.objects.get(id=template_id)
                logger.info(f"[API] Preview mode - using template ID {template_id}: {template_config.template_name}")
            except TemplateConfig.DoesNotExist:
                logger.warning(f"[API] Template ID {template_id} not found")
                return Response({
                    'success': False,
                    'message': f'Template ID {template_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)

        # Priority 2: Active template for specific hotspot
        elif hotspot_name:
            template_config = TemplateConfig.objects.filter(
                hotspot_name=hotspot_name,
                is_active=True
            ).first()

            if template_config:
                logger.info(f"[API] Found hotspot-specific template: {template_config.template_name}")

        # Priority 3: Default active template (no hotspot_name)
        if not template_config:
            template_config = TemplateConfig.objects.filter(
                hotspot_name__isnull=True,
                is_active=True
            ).first()

            if template_config:
                logger.info(f"[API] Using default template: {template_config.template_name}")

        # If no template config found, return default slideshow
        if not template_config:
            logger.warning("[API] No template config found, returning default")
            return Response({
                'success': True,
                'template_name': 'Default Slideshow',
                'left_panel_component': 'slideshow',
                'slides': [],
                'background': {}
            })

        # Build response based on component type
        response_data = {
            'success': True,
            'template_name': template_config.template_name,
            'left_panel_component': template_config.left_panel_component,
        }

        # Get slides if component is slideshow
        if template_config.left_panel_component == 'slideshow':
            try:
                if hotspot_name:
                    slides = SlideContent.objects.filter(hotspot_name=hotspot_name, is_active=True).order_by('order')
                    if not slides.exists():
                        slides = SlideContent.objects.filter(hotspot_name__isnull=True, is_active=True).order_by('order')
                else:
                    slides = SlideContent.objects.filter(hotspot_name__isnull=True, is_active=True).order_by('order')

                slides_data = SlideContentSerializer(slides, many=True, context={'request': request}).data
                response_data['slides'] = [
                    {
                        'icon': slide.get('icon', '📚'),
                        'icon_image_url': slide.get('icon_image_url', ''),
                        'title': slide.get('title', ''),
                        'description': slide.get('description', '')
                    }
                    for slide in slides_data
                ]
                logger.info(f"[API] Loaded {len(response_data['slides'])} slides")
            except Exception as e:
                logger.error(f"[API] Error loading slides: {str(e)}")
                response_data['slides'] = []

        # Get cards if component is cardgallery
        elif template_config.left_panel_component == 'cardgallery':
            try:
                if hotspot_name:
                    cards = CardContent.objects.filter(hotspot_name=hotspot_name, is_active=True).order_by('order')
                    if not cards.exists():
                        cards = CardContent.objects.filter(hotspot_name__isnull=True, is_active=True).order_by('order')
                else:
                    cards = CardContent.objects.filter(hotspot_name__isnull=True, is_active=True).order_by('order')

                cards_data = CardContentSerializer(cards, many=True, context={'request': request}).data
                response_data['cards'] = [
                    {
                        'icon': card.get('icon', '📚'),
                        'icon_image_url': card.get('icon_image_url', ''),
                        'title': card.get('title', ''),
                        'description': card.get('description', '')
                    }
                    for card in cards_data
                ]
                logger.info(f"[API] Loaded {len(response_data['cards'])} cards")
            except Exception as e:
                logger.error(f"[API] Error loading cards: {str(e)}")
                response_data['cards'] = []

        # Get background image
        try:
            if hotspot_name:
                background = BackgroundImage.objects.filter(hotspot_name=hotspot_name, is_active=True).first()
                if not background:
                    background = BackgroundImage.objects.filter(hotspot_name__isnull=True, is_active=True).first()
            else:
                background = BackgroundImage.objects.filter(hotspot_name__isnull=True, is_active=True).first()

            if background:
                serializer = BackgroundImageSerializer(background, context={'request': request})
                response_data['background'] = {
                    'imageUrl': serializer.data['image_url'],
                    'title': serializer.data['title']
                }
                logger.info(f"[API] Loaded background: {background.title}")
            else:
                response_data['background'] = {}
                logger.warning("[API] No background image found")
        except Exception as e:
            logger.error(f"[API] Error loading background: {str(e)}")
            response_data['background'] = {}

        logger.info("[API] Template config loaded successfully")
        return Response(response_data)

    except ValidationError as e:
        logger.error(f"[API] Validation error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Invalid request parameters'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"[API] Unexpected error in get_template_config: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': 'Internal server error. Please try again later.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===============================================
# Hotspot Management API
# ===============================================

class HotspotViewSet(viewsets.ModelViewSet):
    """ViewSet for managing hotspots"""
    queryset = Hotspot.objects.all()
    serializer_class = HotspotSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        """Set created_by when creating a hotspot"""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """
        Test hotspot connection status
        Checks if folder exists, login.html exists, and config matches
        """
        import os
        import re
        from django.conf import settings
        from django.utils import timezone

        hotspot = self.get_object()
        base_dir = settings.BASE_DIR

        try:
            # Check 1: Folder exists
            folder_path = os.path.join(base_dir, hotspot.hotspot_name)
            folder_exists = os.path.isdir(folder_path)

            # Check 2: login.html exists
            login_file_path = os.path.join(folder_path, 'login.html')
            login_file_exists = os.path.isfile(login_file_path)

            # Check 3: Config matched (window.HOTSPOT_NAME)
            config_matched = False
            if login_file_exists:
                try:
                    with open(login_file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Look for window.HOTSPOT_NAME = 'hotspot_xxx';
                        pattern = r"window\.HOTSPOT_NAME\s*=\s*['\"]([^'\"]+)['\"]"
                        match = re.search(pattern, content)
                        if match:
                            found_name = match.group(1)
                            config_matched = (found_name == hotspot.hotspot_name)
                            logger.info(f"[Hotspot Test] Found HOTSPOT_NAME: {found_name}, Expected: {hotspot.hotspot_name}")
                except Exception as e:
                    logger.error(f"[Hotspot Test] Error reading login.html: {str(e)}")

            # Update hotspot status
            hotspot.folder_exists = folder_exists
            hotspot.login_file_exists = login_file_exists
            hotspot.config_matched = config_matched
            hotspot.last_checked = timezone.now()
            hotspot.save()

            logger.info(f"[Hotspot Test] {hotspot.hotspot_name}: folder={folder_exists}, file={login_file_exists}, config={config_matched}")

            return Response({
                'success': True,
                'hotspot': HotspotSerializer(hotspot).data,
                'details': {
                    'folder_path': folder_path,
                    'folder_exists': folder_exists,
                    'login_file_exists': login_file_exists,
                    'config_matched': config_matched,
                    'status': hotspot.status
                }
            })

        except Exception as e:
            logger.error(f"[Hotspot Test] Error testing connection: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': f'Error testing connection: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LandingPageURLViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing landing page URLs

    Features:
    - CRUD operations for landing page URLs
    - Automatic cache invalidation on create/update/delete
    - Only one active URL per hotspot at a time
    """
    queryset = LandingPageURL.objects.all()
    serializer_class = LandingPageURLSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by hotspot_name if provided"""
        queryset = LandingPageURL.objects.all()
        hotspot_name = self.request.query_params.get('hotspot_name', None)
        if hotspot_name:
            queryset = queryset.filter(hotspot_name=hotspot_name)
        return queryset

    def perform_destroy(self, instance):
        """Invalidate cache when deleting a landing URL"""
        hotspot_name = instance.hotspot_name
        instance.delete()

        # Invalidate cache for this hotspot
        cache_key = f'landing_url_{hotspot_name}'
        cache.delete(cache_key)
        logger.info(f"[Landing URL] Deleted and cache invalidated for {hotspot_name}")

    def perform_create(self, serializer):
        """Set created_by when creating a landing URL"""
        hotspot_name = serializer.validated_data.get('hotspot_name')

        # If setting as active, deactivate others for this hotspot
        if serializer.validated_data.get('is_active', False):
            LandingPageURL.objects.filter(
                hotspot_name=hotspot_name,
                is_active=True
            ).update(is_active=False)
            logger.info(f"[Landing URL] Deactivated existing active URLs for {hotspot_name}")

        serializer.save(created_by=self.request.user)

        # Invalidate cache for this hotspot
        cache_key = f'landing_url_{hotspot_name}'
        cache.delete(cache_key)
        logger.info(f"[Landing URL] Cache invalidated for {hotspot_name}")

    def perform_update(self, serializer):
        """Handle activation logic when updating"""
        hotspot_name = serializer.instance.hotspot_name

        if serializer.validated_data.get('is_active', False):
            # Deactivate other active URLs for this hotspot
            LandingPageURL.objects.filter(
                hotspot_name=hotspot_name,
                is_active=True
            ).exclude(id=serializer.instance.id).update(is_active=False)
            logger.info(f"[Landing URL] Deactivated other active URLs for {hotspot_name}")

        serializer.save()

        # Invalidate cache for this hotspot
        cache_key = f'landing_url_{hotspot_name}'
        cache.delete(cache_key)
        logger.info(f"[Landing URL] Cache invalidated for {hotspot_name}")

    @action(detail=True, methods=['post'])
    def set_active(self, request, pk=None):
        """Set this landing URL as active (deactivate others)"""
        landing_url = self.get_object()
        hotspot_name = landing_url.hotspot_name

        # Deactivate other active URLs for this hotspot
        LandingPageURL.objects.filter(
            hotspot_name=hotspot_name,
            is_active=True
        ).exclude(id=landing_url.id).update(is_active=False)

        # Activate this one
        landing_url.is_active = True
        landing_url.save()

        # Invalidate cache for this hotspot
        cache_key = f'landing_url_{hotspot_name}'
        cache.delete(cache_key)

        logger.info(f"[Landing URL] Activated: {landing_url.title} for {hotspot_name}")

        return Response({
            'success': True,
            'message': f'Landing URL "{landing_url.title}" is now active',
            'data': LandingPageURLSerializer(landing_url).data
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_landing_url(request):
    """
    Public API endpoint to get active landing URL for a hotspot
    Used by login.html to determine redirect URL

    Features:
    - Caching: Results cached for 5 minutes per hotspot
    - Error handling: Graceful fallback when no URL configured
    - Auto-invalidation: Cache cleared when landing URLs are updated
    """
    hotspot_name = request.GET.get('hotspot_name', None)

    # Validate hotspot_name parameter
    if not hotspot_name:
        logger.warning("[Landing URL] Missing hotspot_name parameter")
        return Response({
            'success': False,
            'message': 'hotspot_name parameter is required',
            'fallback': True
        }, status=status.HTTP_400_BAD_REQUEST)

    # Validate hotspot_name length (prevent abuse)
    if len(hotspot_name) > 100:
        logger.warning(f"[Landing URL] Invalid hotspot_name length: {len(hotspot_name)}")
        return Response({
            'success': False,
            'message': 'Invalid hotspot_name parameter',
            'fallback': True
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Generate cache key
        cache_key = f'landing_url_{hotspot_name}'

        # Try to get from cache first
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.info(f"[Landing URL] Cache hit for {hotspot_name}")
            return Response(cached_result)

        # Cache miss - query database
        logger.info(f"[Landing URL] Cache miss for {hotspot_name}, querying database")

        landing_url = LandingPageURL.objects.filter(
            hotspot_name=hotspot_name,
            is_active=True
        ).first()

        if landing_url:
            result = {
                'success': True,
                'landing_url': landing_url.url,
                'title': landing_url.title,
                'fallback': False
            }
            logger.info(f"[Landing URL] Found active URL for {hotspot_name}: {landing_url.url}")

            # Update redirect count and timestamp
            landing_url.redirect_count += 1
            landing_url.last_redirected_at = timezone.now()
            landing_url.save(update_fields=['redirect_count', 'last_redirected_at'])
        else:
            result = {
                'success': True,
                'landing_url': None,
                'fallback': True,
                'message': f'No active landing URL configured for {hotspot_name}'
            }
            logger.info(f"[Landing URL] No active URL for {hotspot_name}, using fallback")

        # Cache the result for 5 minutes (300 seconds)
        cache.set(cache_key, result, timeout=300)

        return Response(result)

    except ValidationError as e:
        logger.error(f"[Landing URL] Validation error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Invalid request parameters',
            'fallback': True
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"[Landing URL] Unexpected error: {str(e)}", exc_info=True)
        # Return fallback even on error to ensure login still works
        return Response({
            'success': False,
            'message': 'Internal server error',
            'fallback': True
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_hotspot_choices(request):
    """
    Get hotspot choices for dropdown menus
    Returns list of hotspot objects with full details
    """
    try:
        hotspots = Hotspot.objects.filter(is_active=True).order_by('display_name')
        serializer = HotspotSerializer(hotspots, many=True)
        return Response(serializer.data)

    except Exception as e:
        logger.error(f"[API] Error getting hotspot choices: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': 'Error loading hotspot choices'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===============================================
# Page Impression Tracking API
# ===============================================

def detect_device_type(user_agent):
    """Detect device type from user agent string"""
    if not user_agent:
        return 'unknown'

    ua_lower = user_agent.lower()

    # Check for mobile devices
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipod', 'blackberry', 'windows phone']
    if any(keyword in ua_lower for keyword in mobile_keywords):
        return 'mobile'

    # Check for tablets
    tablet_keywords = ['ipad', 'tablet', 'kindle']
    if any(keyword in ua_lower for keyword in tablet_keywords):
        return 'tablet'

    # Default to desktop
    return 'desktop'


@api_view(['POST'])
@authentication_classes([])  # Disable authentication - allows MikroTik to POST without session
@permission_classes([AllowAny])
def track_impression(request):
    """
    Track page impression (view count)

    Expected data:
    {
        "hotspot_name": "hotspot_lab",
        "mac": "AA:BB:CC:DD:EE:FF",
        "ip": "10.5.50.1",
        "user_agent": "Mozilla/5.0...",
        "time_on_page": 30
    }
    """
    try:
        # Extract data
        hotspot_name = request.data.get('hotspot_name', 'unknown')
        mac = request.data.get('mac', '')
        ip_address = request.data.get('ip', None)
        user_agent = request.data.get('user_agent', '')
        time_on_page = request.data.get('time_on_page', None)

        # Validate required fields
        if not hotspot_name or not mac:
            logger.warning(f"[Tracking] Missing required fields: hotspot_name={hotspot_name}, mac={mac}")
            return Response({
                'success': False,
                'message': 'Missing required fields: hotspot_name and mac'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Hash MAC address for privacy (SHA256)
        mac_hash = hashlib.sha256(mac.encode()).hexdigest()

        # Detect device type
        device_type = detect_device_type(user_agent)

        # Check if this is unique today
        today = date.today()
        is_unique_today = not PageImpression.objects.filter(
            mac_hash=mac_hash,
            hotspot_name=hotspot_name,
            viewed_at__date=today
        ).exists()

        # Create impression record
        impression = PageImpression.objects.create(
            hotspot_name=hotspot_name,
            mac_hash=mac_hash,
            ip_address=ip_address,
            device_type=device_type,
            user_agent=user_agent,
            time_on_page=time_on_page,
            is_unique_today=is_unique_today
        )

        logger.info(f"[Tracking] ✓ Impression recorded: {hotspot_name} | {device_type} | unique={is_unique_today}")

        return Response({
            'success': True,
            'message': 'Impression tracked successfully',
            'is_unique_today': is_unique_today
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"[Tracking] ✗ Error tracking impression: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def impression_statistics(request):
    """Get impression tracking statistics with filtering options"""
    try:
        # Get query parameters
        days = int(request.GET.get('days', 7))  # Default: last 7 days
        hotspot_filter = request.GET.get('hotspot', None)

        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Base queryset
        queryset = PageImpression.objects.filter(viewed_at__gte=start_date)

        # Apply hotspot filter if provided
        if hotspot_filter and hotspot_filter != 'all':
            queryset = queryset.filter(hotspot_name=hotspot_filter)

        # === SUMMARY STATISTICS ===
        total_impressions = queryset.count()
        unique_devices = queryset.values('mac_hash').distinct().count()

        # Average time on page (exclude None/null values)
        avg_time = queryset.filter(time_on_page__isnull=False).aggregate(
            avg=Avg('time_on_page')
        )['avg'] or 0

        # Device breakdown
        device_stats = queryset.values('device_type').annotate(
            count=Count('id')
        ).order_by('-count')

        # Top hotspot by impressions
        top_hotspot = queryset.values('hotspot_name').annotate(
            count=Count('id')
        ).order_by('-count').first()

        # === DAILY TREND (for line chart) ===
        daily_trend = queryset.annotate(
            date=TruncDate('viewed_at')
        ).values('date').annotate(
            total=Count('id'),
            unique=Count('mac_hash', distinct=True)
        ).order_by('date')

        # === HOURLY BREAKDOWN (for heatmap - last 24 hours) ===
        last_24h = timezone.now() - timedelta(hours=24)
        hourly_data = PageImpression.objects.filter(
            viewed_at__gte=last_24h
        ).annotate(
            hour=TruncHour('viewed_at')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour')

        # === HOTSPOT BREAKDOWN (for bar chart) ===
        hotspot_breakdown = queryset.values('hotspot_name').annotate(
            impressions=Count('id'),
            unique_devices=Count('mac_hash', distinct=True)
        ).order_by('-impressions')

        # === RECENT IMPRESSIONS (for table) ===
        recent_limit = int(request.GET.get('limit', 50))
        recent_impressions = queryset.select_related().order_by('-viewed_at')[:recent_limit]

        recent_data = [{
            'id': imp.id,
            'hotspot_name': imp.hotspot_name,
            'viewed_at': imp.viewed_at,
            'device_type': imp.device_type,
            'ip_address': imp.ip_address,
            'time_on_page': imp.time_on_page,
            'is_unique_today': imp.is_unique_today,
            'mac_hash_short': imp.mac_hash[:16] + '...'  # Truncated for display
        } for imp in recent_impressions]

        # Build response
        response_data = {
            'success': True,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            },
            'summary': {
                'total_impressions': total_impressions,
                'unique_devices': unique_devices,
                'avg_time_on_page': round(avg_time, 1),
                'top_hotspot': top_hotspot['hotspot_name'] if top_hotspot else 'N/A',
                'top_hotspot_count': top_hotspot['count'] if top_hotspot else 0
            },
            'device_breakdown': list(device_stats),
            'daily_trend': [{
                'date': item['date'].isoformat(),
                'total': item['total'],
                'unique': item['unique']
            } for item in daily_trend],
            'hourly_data': [{
                'hour': item['hour'].isoformat(),
                'count': item['count']
            } for item in hourly_data],
            'hotspot_breakdown': list(hotspot_breakdown),
            'recent_impressions': recent_data
        }

        logger.info(f"[Stats] Generated statistics: {total_impressions} impressions, {unique_devices} unique devices")
        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"[Stats] Error generating statistics: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': 'Error generating statistics'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def media_reach_report(request):
    """Generate Media Reach Assessment Report for advertising effectiveness"""
    try:
        # Get query parameters
        days = int(request.GET.get('days', 7))
        hotspot_filter = request.GET.get('hotspot', None)
        target_audience = int(request.GET.get('target_audience', 10000))  # Total potential audience

        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Base queryset
        queryset = PageImpression.objects.filter(viewed_at__gte=start_date)

        # Apply hotspot filter if provided
        if hotspot_filter and hotspot_filter != 'all':
            queryset = queryset.filter(hotspot_name=hotspot_filter)

        # === 1. REACH METRICS ===

        # Total Reach (Unique Devices)
        total_reach = queryset.values('mac_hash').distinct().count()

        # Total Impressions (OTS - Opportunity To See)
        total_impressions = queryset.count()

        # Frequency (Average exposures per person)
        frequency = round(total_impressions / total_reach, 1) if total_reach > 0 else 0

        # Reach Rate (% of target audience)
        reach_rate = round((total_reach / target_audience * 100), 1) if target_audience > 0 else 0

        # GRP (Gross Rating Point)
        grp = round(reach_rate * frequency, 0)

        # === 2. EFFECTIVE REACH ===

        # Frequency distribution
        frequency_dist = queryset.values('mac_hash').annotate(
            impression_count=Count('id')
        ).values('impression_count').annotate(
            users=Count('mac_hash')
        ).order_by('impression_count')

        # Categorize by frequency buckets
        freq_1_2 = sum(item['users'] for item in frequency_dist if 1 <= item['impression_count'] <= 2)
        freq_3_7 = sum(item['users'] for item in frequency_dist if 3 <= item['impression_count'] <= 7)
        freq_8_15 = sum(item['users'] for item in frequency_dist if 8 <= item['impression_count'] <= 15)
        freq_15_plus = sum(item['users'] for item in frequency_dist if item['impression_count'] > 15)

        # Effective Reach (3+ exposures)
        effective_reach = freq_3_7 + freq_8_15 + freq_15_plus
        effective_reach_percentage = round((effective_reach / total_reach * 100), 1) if total_reach > 0 else 0

        # === 3. ENGAGEMENT METRICS ===

        # Average Time on Page
        avg_time_on_page = queryset.filter(
            time_on_page__isnull=False
        ).aggregate(avg=Avg('time_on_page'))['avg'] or 0

        # Engagement Rate (users who stayed >10 seconds)
        engaged_users = queryset.filter(time_on_page__gte=10).count()
        engagement_rate = round((engaged_users / total_impressions * 100), 1) if total_impressions > 0 else 0

        # === 4. DEVICE-BASED REACH ===

        device_reach = queryset.values('device_type').annotate(
            unique_users=Count('mac_hash', distinct=True),
            total_impressions=Count('id'),
            avg_time=Avg('time_on_page')
        ).order_by('-total_impressions')

        # === 5. TIME-BASED REACH ===

        # Peak day
        daily_stats = queryset.annotate(
            date=TruncDate('viewed_at')
        ).values('date').annotate(
            impressions=Count('id'),
            unique_users=Count('mac_hash', distinct=True)
        ).order_by('-impressions').first()

        # Peak hour
        hourly_stats = queryset.annotate(
            hour=TruncHour('viewed_at')
        ).values('hour').annotate(
            impressions=Count('id')
        ).order_by('-impressions').first()

        # === 6. LOCATION-BASED REACH ===

        location_reach = queryset.values('hotspot_name').annotate(
            unique_users=Count('mac_hash', distinct=True),
            total_impressions=Count('id'),
            avg_frequency=Count('id') * 1.0 / Count('mac_hash', distinct=True)
        ).order_by('-total_impressions')

        # Calculate CPM (Cost Per Mille) if cost provided
        ad_cost = float(request.GET.get('ad_cost', 0))
        cpm = round((ad_cost / total_impressions * 1000), 2) if total_impressions > 0 and ad_cost > 0 else 0

        # === 7. COMPARATIVE METRICS ===

        # Compare with previous period
        prev_start = start_date - timedelta(days=days)
        prev_end = start_date

        prev_queryset = PageImpression.objects.filter(
            viewed_at__gte=prev_start,
            viewed_at__lt=prev_end
        )
        if hotspot_filter and hotspot_filter != 'all':
            prev_queryset = prev_queryset.filter(hotspot_name=hotspot_filter)

        prev_reach = prev_queryset.values('mac_hash').distinct().count()
        prev_impressions = prev_queryset.count()

        reach_growth = round(((total_reach - prev_reach) / prev_reach * 100), 1) if prev_reach > 0 else 0
        impression_growth = round(((total_impressions - prev_impressions) / prev_impressions * 100), 1) if prev_impressions > 0 else 0

        # Build response
        response_data = {
            'success': True,
            'report_period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            },
            'reach_metrics': {
                'total_reach': total_reach,
                'reach_rate': reach_rate,
                'total_impressions': total_impressions,
                'frequency': frequency,
                'grp': grp,
                'target_audience': target_audience
            },
            'effective_reach': {
                'total': effective_reach,
                'percentage': effective_reach_percentage,
                'frequency_distribution': {
                    'low_1_2': {'users': freq_1_2, 'percentage': round(freq_1_2 / total_reach * 100, 1) if total_reach > 0 else 0},
                    'optimal_3_7': {'users': freq_3_7, 'percentage': round(freq_3_7 / total_reach * 100, 1) if total_reach > 0 else 0},
                    'high_8_15': {'users': freq_8_15, 'percentage': round(freq_8_15 / total_reach * 100, 1) if total_reach > 0 else 0},
                    'overexposed_15_plus': {'users': freq_15_plus, 'percentage': round(freq_15_plus / total_reach * 100, 1) if total_reach > 0 else 0}
                }
            },
            'engagement': {
                'avg_time_on_page': round(avg_time_on_page, 1),
                'engagement_rate': engagement_rate,
                'engaged_users': engaged_users
            },
            'device_breakdown': [{
                'device_type': item['device_type'] or 'unknown',
                'unique_users': item['unique_users'],
                'total_impressions': item['total_impressions'],
                'avg_time': round(item['avg_time'], 1) if item['avg_time'] else 0,
                'percentage': round(item['total_impressions'] / total_impressions * 100, 1) if total_impressions > 0 else 0
            } for item in device_reach],
            'peak_performance': {
                'best_day': {
                    'date': daily_stats['date'].isoformat() if daily_stats else None,
                    'impressions': daily_stats['impressions'] if daily_stats else 0,
                    'unique_users': daily_stats['unique_users'] if daily_stats else 0
                },
                'best_hour': {
                    'hour': hourly_stats['hour'].isoformat() if hourly_stats else None,
                    'impressions': hourly_stats['impressions'] if hourly_stats else 0
                }
            },
            'location_breakdown': [{
                'hotspot': item['hotspot_name'],
                'unique_users': item['unique_users'],
                'total_impressions': item['total_impressions'],
                'avg_frequency': round(item['avg_frequency'], 1),
                'percentage': round(item['total_impressions'] / total_impressions * 100, 1) if total_impressions > 0 else 0
            } for item in location_reach],
            'cost_analysis': {
                'ad_cost': ad_cost,
                'cpm': cpm,
                'cost_per_reach': round(ad_cost / total_reach, 2) if total_reach > 0 and ad_cost > 0 else 0
            },
            'growth_comparison': {
                'reach_growth': reach_growth,
                'impression_growth': impression_growth,
                'previous_period': {
                    'reach': prev_reach,
                    'impressions': prev_impressions
                }
            },
            'recommendations': generate_recommendations(
                frequency, effective_reach_percentage, engagement_rate, freq_15_plus, total_reach
            )
        }

        logger.info(f"[Media Reach] Generated report: Reach={total_reach}, GRP={grp}, Effective={effective_reach_percentage}%")
        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"[Media Reach] Error generating report: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': 'Error generating media reach report'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def generate_recommendations(frequency, effective_reach_pct, engagement_rate, overexposed_count, total_reach):
    """Generate actionable recommendations based on metrics"""
    recommendations = []

    # Frequency recommendations
    if frequency < 3:
        recommendations.append({
            'type': 'warning',
            'category': 'Frequency',
            'message': f'Average frequency ({frequency}x) is low. Consider extending campaign duration or increasing ad placement.',
            'action': 'Increase exposure frequency to 3-7x for better recall'
        })
    elif frequency > 15:
        recommendations.append({
            'type': 'warning',
            'category': 'Frequency',
            'message': f'Average frequency ({frequency}x) is very high. Risk of ad fatigue.',
            'action': 'Rotate creative or reduce frequency to avoid audience burnout'
        })
    else:
        recommendations.append({
            'type': 'success',
            'category': 'Frequency',
            'message': f'Frequency ({frequency}x) is optimal for brand recall',
            'action': 'Continue current strategy'
        })

    # Effective reach recommendations
    if effective_reach_pct < 50:
        recommendations.append({
            'type': 'danger',
            'category': 'Effective Reach',
            'message': f'Only {effective_reach_pct}% of audience reached effectively (3+ exposures)',
            'action': 'Extend campaign duration or increase touchpoints'
        })
    elif effective_reach_pct >= 70:
        recommendations.append({
            'type': 'success',
            'category': 'Effective Reach',
            'message': f'Excellent effective reach at {effective_reach_pct}%',
            'action': 'Maintain current coverage strategy'
        })

    # Engagement recommendations
    if engagement_rate < 30:
        recommendations.append({
            'type': 'warning',
            'category': 'Engagement',
            'message': f'Low engagement rate ({engagement_rate}%). Users may be skipping quickly.',
            'action': 'Improve creative design or simplify message'
        })
    elif engagement_rate >= 50:
        recommendations.append({
            'type': 'success',
            'category': 'Engagement',
            'message': f'Strong engagement at {engagement_rate}%',
            'action': 'Creative is resonating well with audience'
        })

    # Overexposure check
    if overexposed_count > 0:
        overexposed_pct = round(overexposed_count / total_reach * 100, 1) if total_reach > 0 else 0
        if overexposed_pct > 10:
            recommendations.append({
                'type': 'warning',
                'category': 'Overexposure',
                'message': f'{overexposed_pct}% of users saw ad 15+ times',
                'action': 'Implement frequency capping or rotate creative more frequently'
            })

    return recommendations


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_reach_report_pdf(request):
    """Export Media Reach Report as PDF"""
    try:
        # Get same parameters as media_reach_report
        days = int(request.GET.get('days', 7))
        hotspot_filter = request.GET.get('hotspot', None)
        target_audience = int(request.GET.get('target_audience', 10000))

        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Get data (reuse logic from media_reach_report)
        queryset = PageImpression.objects.filter(viewed_at__gte=start_date)
        if hotspot_filter and hotspot_filter != 'all':
            queryset = queryset.filter(hotspot_name=hotspot_filter)

        # Calculate metrics
        total_reach = queryset.values('mac_hash').distinct().count()
        total_impressions = queryset.count()
        frequency = round(total_impressions / total_reach, 1) if total_reach > 0 else 0
        reach_rate = round((total_reach / target_audience * 100), 1) if target_audience > 0 else 0
        grp = round(reach_rate * frequency, 0)

        # Frequency distribution
        frequency_dist = queryset.values('mac_hash').annotate(
            impression_count=Count('id')
        ).values('impression_count').annotate(
            users=Count('mac_hash')
        ).order_by('impression_count')

        freq_1_2 = sum(item['users'] for item in frequency_dist if 1 <= item['impression_count'] <= 2)
        freq_3_7 = sum(item['users'] for item in frequency_dist if 3 <= item['impression_count'] <= 7)
        freq_8_15 = sum(item['users'] for item in frequency_dist if 8 <= item['impression_count'] <= 15)
        freq_15_plus = sum(item['users'] for item in frequency_dist if item['impression_count'] > 15)
        effective_reach = freq_3_7 + freq_8_15 + freq_15_plus
        effective_reach_percentage = round((effective_reach / total_reach * 100), 1) if total_reach > 0 else 0

        # Engagement
        avg_time_on_page = queryset.filter(time_on_page__isnull=False).aggregate(avg=Avg('time_on_page'))['avg'] or 0
        engaged_users = queryset.filter(time_on_page__gte=10).count()
        engagement_rate = round((engaged_users / total_impressions * 100), 1) if total_impressions > 0 else 0

        # Device breakdown
        device_reach = queryset.values('device_type').annotate(
            unique_users=Count('mac_hash', distinct=True),
            total_impressions=Count('id')
        ).order_by('-total_impressions')

        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                              rightMargin=0.75*inch, leftMargin=0.75*inch,
                              topMargin=1*inch, bottomMargin=0.75*inch)

        # Register Thai fonts
        register_thai_fonts()

        # Container for PDF elements
        elements = []
        styles = getSampleStyleSheet()

        # Custom styles with Thai font support
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName='THSarabun-Bold',
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontName='THSarabun-Bold',
            fontSize=16,
            textColor=colors.HexColor('#3498db'),
            spaceAfter=12,
            spaceBefore=12
        )

        normal_style = ParagraphStyle(
            'ThaiNormal',
            parent=styles['Normal'],
            fontName='THSarabun',
            fontSize=14
        )

        # Add Logo and Organization Name from SystemSettings
        try:
            system_settings = SystemSettings.objects.first()
            if system_settings:
                if system_settings.logo:
                    logo_path = system_settings.logo.path
                    if os.path.exists(logo_path):
                        # Add logo (max width 2 inches, maintain aspect ratio)
                        logo = Image(logo_path, width=2*inch, height=0.8*inch, kind='proportional')
                        elements.append(logo)
                        elements.append(Spacer(1, 0.1*inch))

                # Add organization name if available
                if system_settings.organization_name:
                    org_style = ParagraphStyle(
                        'OrgName',
                        parent=styles['Normal'],
                        fontName='THSarabun-Bold',
                        fontSize=16,
                        textColor=colors.HexColor('#2c3e50'),
                        alignment=TA_CENTER,
                        spaceAfter=6
                    )
                    elements.append(Paragraph(system_settings.organization_name, org_style))
                    elements.append(Spacer(1, 0.1*inch))
        except Exception as e:
            logger.warning(f"[PDF] Could not add logo/org name: {str(e)}")

        # Title
        elements.append(Paragraph("รายงานการประเมินผลการเข้าถึงสื่อ (Media Reach Assessment Report)", title_style))
        elements.append(Paragraph(f"ช่วงเวลา: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}", normal_style))
        elements.append(Spacer(1, 0.3*inch))

        # Key Metrics Summary Table
        elements.append(Paragraph("1. Key Metrics Summary", heading_style))

        key_metrics_data = [
            ['Metric', 'Value', 'Metric', 'Value'],
            ['Total Reach', f'{total_reach:,} users', 'Reach Rate', f'{reach_rate}%'],
            ['Total Impressions', f'{total_impressions:,}', 'Frequency', f'{frequency}x'],
            ['GRP', str(grp), 'Effective Reach', f'{effective_reach:,} ({effective_reach_percentage}%)'],
            ['Avg Time on Page', f'{round(avg_time_on_page, 1)}s', 'Engagement Rate', f'{engagement_rate}%'],
        ]

        key_metrics_table = Table(key_metrics_data, colWidths=[2*inch, 1.5*inch, 2*inch, 1.5*inch])
        key_metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'THSarabun-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#ecf0f1')),
            ('BACKGROUND', (2, 1), (2, -1), colors.HexColor('#ecf0f1')),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (0, -1), 'THSarabun-Bold'),
            ('FONTNAME', (2, 1), (2, -1), 'THSarabun-Bold'),
            ('FONTNAME', (1, 1), (1, -1), 'THSarabun'),
            ('FONTNAME', (3, 1), (3, -1), 'THSarabun'),
            ('FONTSIZE', (0, 1), (-1, -1), 14),
        ]))
        elements.append(key_metrics_table)
        elements.append(Spacer(1, 0.3*inch))

        # Frequency Distribution
        elements.append(Paragraph("2. Frequency Distribution", heading_style))

        freq_data = [
            ['Exposure Frequency', 'Users', 'Percentage', 'Status'],
            ['1-2 Times', f'{freq_1_2:,}', f'{round(freq_1_2/total_reach*100,1) if total_reach>0 else 0}%', 'Low'],
            ['3-7 Times', f'{freq_3_7:,}', f'{round(freq_3_7/total_reach*100,1) if total_reach>0 else 0}%', 'Optimal ⭐'],
            ['8-15 Times', f'{freq_8_15:,}', f'{round(freq_8_15/total_reach*100,1) if total_reach>0 else 0}%', 'High'],
            ['15+ Times', f'{freq_15_plus:,}', f'{round(freq_15_plus/total_reach*100,1) if total_reach>0 else 0}%', 'Overexposed'],
        ]

        freq_table = Table(freq_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        freq_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'THSarabun-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#fff9e6')),  # Low
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#e6ffe6')),  # Optimal
            ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#e6f2ff')),  # High
            ('FONTNAME', (0, 1), (-1, -1), 'THSarabun'),
            ('FONTSIZE', (0, 1), (-1, -1), 14),
            ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#ffe6e6')),  # Overexposed
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(freq_table)
        elements.append(Spacer(1, 0.3*inch))

        # Device Breakdown
        elements.append(Paragraph("3. Device Breakdown", heading_style))

        device_data = [['Device Type', 'Unique Users', 'Total Impressions', 'Percentage']]
        for device in device_reach:
            device_type = device['device_type'] or 'unknown'
            device_pct = round(device['total_impressions'] / total_impressions * 100, 1) if total_impressions > 0 else 0
            device_data.append([
                device_type.capitalize(),
                f"{device['unique_users']:,}",
                f"{device['total_impressions']:,}",
                f"{device_pct}%"
            ])

        device_table = Table(device_data, colWidths=[2*inch, 1.5*inch, 1.8*inch, 1.2*inch])
        device_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'THSarabun-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('FONTNAME', (0, 1), (-1, -1), 'THSarabun'),
            ('FONTSIZE', (0, 1), (-1, -1), 14),
        ]))
        elements.append(device_table)
        elements.append(Spacer(1, 0.3*inch))

        # Recommendations
        recommendations = generate_recommendations(frequency, effective_reach_percentage, engagement_rate, freq_15_plus, total_reach)
        if recommendations:
            elements.append(Paragraph("4. Recommendations", heading_style))

            # Recommendation style
            rec_style = ParagraphStyle(
                'ThaiRec',
                parent=styles['Normal'],
                fontName='THSarabun',
                fontSize=14,
                leading=18
            )

            for i, rec in enumerate(recommendations, 1):
                icon = {'success': '✓', 'warning': '⚠', 'danger': '✗', 'info': 'ℹ'}[rec['type']]
                rec_text = f"<b>{icon} {rec['category']}:</b> {rec['message']}<br/><i>Action: {rec['action']}</i>"
                elements.append(Paragraph(rec_text, rec_style))
                elements.append(Spacer(1, 0.1*inch))

        # Footer
        elements.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontName='THSarabun', fontSize=12, textColor=colors.grey, alignment=TA_CENTER)
        elements.append(Paragraph(f"สร้างเมื่อ: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')} | LibLogin Monitoring System", footer_style))

        # Build PDF
        doc.build(elements)

        # Get PDF from buffer
        pdf = buffer.getvalue()
        buffer.close()

        # Create HTTP response with inline display
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="media_reach_report_{start_date.strftime("%Y%m%d")}-{end_date.strftime("%Y%m%d")}.pdf"'
        response.write(pdf)

        logger.info(f"[PDF Export] Media Reach Report exported successfully")
        return response

    except Exception as e:
        logger.error(f"[PDF Export] Error: {str(e)}", exc_info=True)
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)
