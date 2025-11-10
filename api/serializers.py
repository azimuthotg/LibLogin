from rest_framework import serializers
from django.contrib.auth.models import User
from .models import BackgroundImage, SystemSettings


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
        fields = ['id', 'title', 'image', 'image_url', 'router_id', 'is_active',
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
        fields = ['title', 'image', 'router_id', 'is_active']


class SystemSettingsSerializer(serializers.ModelSerializer):
    """Serializer for SystemSettings model"""
    updated_by = UserSerializer(read_only=True)
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = SystemSettings
        fields = ['id', 'library_name', 'contact_info', 'logo', 'logo_url',
                  'default_router_id', 'updated_at', 'updated_by']
        read_only_fields = ['id', 'updated_at']

    def get_logo_url(self, obj):
        """Return full URL for the logo"""
        request = self.context.get('request')
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        return None
