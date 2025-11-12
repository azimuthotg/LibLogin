from django.db import models
from django.contrib.auth.models import User
from PIL import Image
import os


class BackgroundImage(models.Model):
    """Model for storing background images"""
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='backgrounds/')
    router_id = models.CharField(max_length=100, blank=True, null=True, help_text="Router ID for specific device")
    is_active = models.BooleanField(default=False, help_text="Set as current background")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_images')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} - {'Active' if self.is_active else 'Inactive'}"

    def save(self, *args, **kwargs):
        # If this image is set as active, deactivate all other images for the same router
        if self.is_active:
            BackgroundImage.objects.filter(router_id=self.router_id, is_active=True).exclude(id=self.id).update(is_active=False)

        super().save(*args, **kwargs)

        # Optimize image after upload
        if self.image:
            img_path = self.image.path
            img = Image.open(img_path)

            # Resize if too large (max 1920x1080)
            max_size = (1920, 1080)
            if img.height > max_size[1] or img.width > max_size[0]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img.save(img_path, optimize=True, quality=85)


class SlideContent(models.Model):
    """Model for storing slide show content on login page"""
    icon = models.CharField(max_length=10, default="📚", help_text="Emoji icon (e.g., 📚, 📖, 💻)")
    title = models.CharField(max_length=255, help_text="Slide title")
    description = models.TextField(help_text="Slide description")
    router_id = models.CharField(max_length=100, blank=True, null=True, help_text="Router ID for specific device (blank = all routers)")
    order = models.IntegerField(default=0, help_text="Display order (lower numbers shown first)")
    is_active = models.BooleanField(default=True, help_text="Show this slide")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_slides')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "Slide Content"
        verbose_name_plural = "Slide Contents"

    def __str__(self):
        router_info = f" ({self.router_id})" if self.router_id else " (All Routers)"
        status = "✓" if self.is_active else "✗"
        return f"{status} {self.title}{router_info}"


class SystemSettings(models.Model):
    """Model for storing system settings"""
    library_name = models.CharField(max_length=255, default="Library Login System")
    contact_info = models.TextField(blank=True, help_text="Contact information for support")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    default_router_id = models.CharField(max_length=100, blank=True, help_text="Default router ID")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"

    def __str__(self):
        return self.library_name
