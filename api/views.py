from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import BackgroundImage, SystemSettings, SlideContent, TemplateConfig, CardContent
from .serializers import (
    BackgroundImageSerializer,
    BackgroundImageUploadSerializer,
    SystemSettingsSerializer,
    UserSerializer,
    TemplateConfigSerializer,
    TemplateConfigFullSerializer,
    SlideContentSerializer,
    CardContentSerializer
)
import logging

# Configure logging
logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_background_image(request):
    """
    Public API endpoint to get the current active background image
    Supports router_id parameter for device-specific backgrounds
    """
    router_id = request.GET.get('router_id', None)

    try:
        logger.info(f"[API] get_background_image called with router_id={router_id}")

        # Validate router_id if provided
        if router_id and len(router_id) > 100:
            logger.warning(f"[API] Invalid router_id length: {len(router_id)}")
            return Response({
                'success': False,
                'message': 'Invalid router_id parameter'
            }, status=status.HTTP_400_BAD_REQUEST)

        background = None

        # Try to get active background for specific router
        if router_id:
            background = BackgroundImage.objects.filter(
                router_id=router_id,
                is_active=True
            ).first()

            if background:
                logger.info(f"[API] Found router-specific background: {background.title}")

        # Fallback to default background (no router_id)
        if not background:
            background = BackgroundImage.objects.filter(
                router_id__isnull=True,
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
        """Get images filtered by router_id"""
        router_id = request.query_params.get('router_id', None)
        if router_id:
            images = self.queryset.filter(router_id=router_id)
        else:
            images = self.queryset.filter(router_id__isnull=True)

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
    Supports router_id parameter for device-specific slides
    Returns all active slides ordered by 'order' field
    """
    router_id = request.GET.get('router_id', None)

    try:
        # Get active slides for specific router
        if router_id:
            slides = SlideContent.objects.filter(
                router_id=router_id,
                is_active=True
            )
        else:
            # Get default slides (no router_id)
            slides = SlideContent.objects.filter(
                router_id__isnull=True,
                is_active=True
            )

        # If no router-specific slides found, try default slides
        if router_id and not slides.exists():
            slides = SlideContent.objects.filter(
                router_id__isnull=True,
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
    Returns template type, slides, cards, and background based on router_id or template_id

    Parameters:
    - template_id: Specific template ID for preview (optional)
    - router_id: Router ID for device-specific templates (optional)

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
    router_id = request.GET.get('router_id', None)
    template_id = request.GET.get('template_id', None)

    try:
        logger.info(f"[API] get_template_config called with router_id={router_id}, template_id={template_id}")

        # Validate router_id if provided
        if router_id and len(router_id) > 100:
            logger.warning(f"[API] Invalid router_id length: {len(router_id)}")
            return Response({
                'success': False,
                'message': 'Invalid router_id parameter'
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

        # Priority 2: Active template for specific router
        elif router_id:
            template_config = TemplateConfig.objects.filter(
                router_id=router_id,
                is_active=True
            ).first()

            if template_config:
                logger.info(f"[API] Found router-specific template: {template_config.template_name}")

        # Priority 3: Default active template (no router_id)
        if not template_config:
            template_config = TemplateConfig.objects.filter(
                router_id__isnull=True,
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
                if router_id:
                    slides = SlideContent.objects.filter(router_id=router_id, is_active=True).order_by('order')
                    if not slides.exists():
                        slides = SlideContent.objects.filter(router_id__isnull=True, is_active=True).order_by('order')
                else:
                    slides = SlideContent.objects.filter(router_id__isnull=True, is_active=True).order_by('order')

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
                if router_id:
                    cards = CardContent.objects.filter(router_id=router_id, is_active=True).order_by('order')
                    if not cards.exists():
                        cards = CardContent.objects.filter(router_id__isnull=True, is_active=True).order_by('order')
                else:
                    cards = CardContent.objects.filter(router_id__isnull=True, is_active=True).order_by('order')

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
            if router_id:
                background = BackgroundImage.objects.filter(router_id=router_id, is_active=True).first()
                if not background:
                    background = BackgroundImage.objects.filter(router_id__isnull=True, is_active=True).first()
            else:
                background = BackgroundImage.objects.filter(router_id__isnull=True, is_active=True).first()

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
