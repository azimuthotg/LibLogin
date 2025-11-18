from rest_framework import serializers
from django.contrib.auth.models import User
from .models import BackgroundImage, SystemSettings, TemplateConfig, SlideContent, CardContent, Hotspot


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']
        read_only_fields = ['id']


class BackgroundImageSerializer(serializers.ModelSerializer):
    """Serializer for BackgroundImage model"""
    uploaded_by = UserSerializer(read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = BackgroundImage
        fields = ['id', 'title', 'image', 'image_url', 'hotspot_name', 'is_active',
                  'uploaded_by', 'uploaded_at', 'updated_at']
        read_only_fields = ['id', 'uploaded_at', 'updated_at']

    def get_image_url(self, obj):
        """Return full URL for the image"""
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class BackgroundImageUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading background images"""
    class Meta:
        model = BackgroundImage
        fields = ['title', 'image', 'hotspot_name', 'is_active']


class HotspotSerializer(serializers.ModelSerializer):
    """Serializer for Hotspot model"""
    created_by = UserSerializer(read_only=True)
    status = serializers.ReadOnlyField()
    status_icon = serializers.ReadOnlyField()

    class Meta:
        model = Hotspot
        fields = ['id', 'hotspot_name', 'display_name', 'description', 'is_active',
                  'folder_exists', 'login_file_exists', 'config_matched', 'last_checked',
                  'status', 'status_icon', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'folder_exists', 'login_file_exists', 'config_matched',
                            'last_checked', 'created_at', 'updated_at', 'status', 'status_icon']


class HotspotChoiceSerializer(serializers.Serializer):
    """Serializer for hotspot choices (for dropdowns)"""
    value = serializers.CharField()
    label = serializers.CharField()


class SystemSettingsSerializer(serializers.ModelSerializer):
    """Serializer for SystemSettings model"""
    updated_by = UserSerializer(read_only=True)
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = SystemSettings
        fields = ['id', 'organization_name', 'library_name', 'contact_info', 'logo', 'logo_url',
                  'default_hotspot_name', 'hotspot_status_refresh_interval',
                  'updated_at', 'updated_by']
        read_only_fields = ['id', 'updated_at']

    def get_logo_url(self, obj):
        """Return full URL for the logo"""
        request = self.context.get('request')
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        return None


class TemplateConfigSerializer(serializers.ModelSerializer):
    """Serializer for TemplateConfig model"""
    created_by = UserSerializer(read_only=True)
    component_display = serializers.CharField(source='get_left_panel_component_display', read_only=True)

    class Meta:
        model = TemplateConfig
        fields = ['id', 'template_name', 'left_panel_component', 'component_display',
                  'hotspot_name', 'is_active', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SlideContentSerializer(serializers.ModelSerializer):
    """Serializer for SlideContent model"""
    created_by = UserSerializer(read_only=True)
    icon_image_url = serializers.SerializerMethodField()

    class Meta:
        model = SlideContent
        fields = ['id', 'icon', 'icon_image', 'icon_image_url', 'title', 'description',
                  'hotspot_name', 'order', 'is_active', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_icon_image_url(self, obj):
        """Return full URL for the icon image"""
        request = self.context.get('request')
        if obj.icon_image and request:
            return request.build_absolute_uri(obj.icon_image.url)
        return None


class CardContentSerializer(serializers.ModelSerializer):
    """Serializer for CardContent model"""
    created_by = UserSerializer(read_only=True)
    icon_image_url = serializers.SerializerMethodField()

    class Meta:
        model = CardContent
        fields = ['id', 'icon', 'icon_image', 'icon_image_url', 'title', 'description',
                  'hotspot_name', 'order', 'is_active', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_icon_image_url(self, obj):
        """Return full URL for the icon image"""
        request = self.context.get('request')
        if obj.icon_image and request:
            return request.build_absolute_uri(obj.icon_image.url)
        return None


class TemplateConfigFullSerializer(serializers.Serializer):
    """Combined serializer for template configuration with all related content"""
    template_name = serializers.CharField()
    left_panel_component = serializers.CharField()
    slides = SlideContentSerializer(many=True, required=False)
    cards = CardContentSerializer(many=True, required=False)
    background = serializers.DictField(required=False)
