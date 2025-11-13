from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User
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


@api_view(['GET'])
@permission_classes([AllowAny])
def get_background_image(request):
    """
    Public API endpoint to get the current active background image
    Supports router_id parameter for device-specific backgrounds
    """
    router_id = request.GET.get('router_id', None)

    try:
        # Try to get active background for specific router
        if router_id:
            background = BackgroundImage.objects.filter(
                router_id=router_id,
                is_active=True
            ).first()

        # Fallback to default background (no router_id)
        if not router_id or not background:
            background = BackgroundImage.objects.filter(
                router_id__isnull=True,
                is_active=True
            ).first()

        if background:
            serializer = BackgroundImageSerializer(background, context={'request': request})
            return Response({
                'success': True,
                'imageUrl': serializer.data['image_url'],
                'title': serializer.data['title']
            })
        else:
            return Response({
                'success': False,
                'message': 'No active background image found'
            }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
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
    Returns template type, slides, cards, and background based on router_id

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

    try:
        # Get active template config for router
        template_config = None
        if router_id:
            template_config = TemplateConfig.objects.filter(
                router_id=router_id,
                is_active=True
            ).first()

        # Fallback to default template (no router_id)
        if not template_config:
            template_config = TemplateConfig.objects.filter(
                router_id__isnull=True,
                is_active=True
            ).first()

        # If no template config found, return default slideshow
        if not template_config:
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
            if router_id:
                slides = SlideContent.objects.filter(router_id=router_id, is_active=True)
                if not slides.exists():
                    slides = SlideContent.objects.filter(router_id__isnull=True, is_active=True)
            else:
                slides = SlideContent.objects.filter(router_id__isnull=True, is_active=True)

            slides_data = SlideContentSerializer(slides, many=True, context={'request': request}).data
            response_data['slides'] = [
                {
                    'icon': slide['icon'],
                    'icon_image_url': slide['icon_image_url'],
                    'title': slide['title'],
                    'description': slide['description']
                }
                for slide in slides_data
            ]

        # Get cards if component is cardgallery
        elif template_config.left_panel_component == 'cardgallery':
            if router_id:
                cards = CardContent.objects.filter(router_id=router_id, is_active=True)
                if not cards.exists():
                    cards = CardContent.objects.filter(router_id__isnull=True, is_active=True)
            else:
                cards = CardContent.objects.filter(router_id__isnull=True, is_active=True)

            cards_data = CardContentSerializer(cards, many=True, context={'request': request}).data
            response_data['cards'] = [
                {
                    'icon': card['icon'],
                    'icon_image_url': card['icon_image_url'],
                    'title': card['title'],
                    'description': card['description']
                }
                for card in cards_data
            ]

        # Get background image
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
        else:
            response_data['background'] = {}

        return Response(response_data)

    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
