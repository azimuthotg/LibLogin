from django.db import models
from django.contrib.auth.models import User
from PIL import Image
import os


class BackgroundImage(models.Model):
    """Model for storing background images"""
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='backgrounds/')
    hotspot_name = models.CharField(max_length=100, blank=True, null=True, help_text="Hotspot name (e.g., 'hotspot', 'hotspot_lib') - blank for all hotspots")
    is_active = models.BooleanField(default=False, help_text="Set as current background")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_images')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} - {'Active' if self.is_active else 'Inactive'}"

    def save(self, *args, **kwargs):
        # If this image is set as active, deactivate all other images for the same hotspot
        if self.is_active:
            BackgroundImage.objects.filter(hotspot_name=self.hotspot_name, is_active=True).exclude(id=self.id).update(is_active=False)

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


class TemplateConfig(models.Model):
    """Model for configuring login page templates"""
    COMPONENT_CHOICES = [
        ('slideshow', 'Slideshow (Icons + Text + Dots)'),
        ('fullbg', 'Full Background (No Text Overlay)'),
        ('cardgallery', 'Card Gallery (Grid of Cards)'),
    ]

    template_name = models.CharField(max_length=255, help_text="Template name for identification")
    left_panel_component = models.CharField(
        max_length=50,
        choices=COMPONENT_CHOICES,
        default='slideshow',
        help_text="Component type for left panel"
    )
    hotspot_name = models.CharField(max_length=100, blank=True, null=True, help_text="Hotspot name (e.g., 'hotspot', 'hotspot_lib') - blank for all hotspots")
    is_active = models.BooleanField(default=False, help_text="Set as active template for this hotspot")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Template Configuration"
        verbose_name_plural = "Template Configurations"

    def __str__(self):
        hotspot_info = f" ({self.hotspot_name})" if self.hotspot_name else " (All Hotspots)"
        status = "✓" if self.is_active else "✗"
        return f"{status} {self.template_name}{hotspot_info} - {self.get_left_panel_component_display()}"

    def save(self, *args, **kwargs):
        # If this template is set as active, deactivate all other templates for the same hotspot
        if self.is_active:
            TemplateConfig.objects.filter(hotspot_name=self.hotspot_name, is_active=True).exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)


class SlideContent(models.Model):
    """Model for storing slide show content on login page"""
    icon = models.CharField(max_length=10, default="📚", blank=True, help_text="Emoji icon (e.g., 📚, 📖, 💻) - optional if using image")
    icon_image = models.ImageField(upload_to='slide_icons/', blank=True, null=True, help_text="Icon image file (recommended size: 100x100px)")
    title = models.CharField(max_length=255, help_text="Slide title")
    description = models.TextField(help_text="Slide description")
    hotspot_name = models.CharField(max_length=100, blank=True, null=True, help_text="Hotspot name (e.g., 'hotspot', 'hotspot_lib') - blank for all hotspots")
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
        hotspot_info = f" ({self.hotspot_name})" if self.hotspot_name else " (All Hotspots)"
        status = "✓" if self.is_active else "✗"
        return f"{status} {self.title}{hotspot_info}"

    def get_icon_display(self):
        """Return icon image URL if exists, otherwise return emoji"""
        if self.icon_image:
            return self.icon_image.url
        return self.icon


class CardContent(models.Model):
    """Model for storing card content for card gallery component"""
    icon = models.CharField(max_length=10, default="📚", blank=True, help_text="Emoji icon (e.g., 📚, 💻, 🎓) - optional if using image")
    icon_image = models.ImageField(upload_to='card_icons/', blank=True, null=True, help_text="Icon image file (recommended size: 100x100px)")
    title = models.CharField(max_length=255, help_text="Card title")
    description = models.TextField(help_text="Card description")
    hotspot_name = models.CharField(max_length=100, blank=True, null=True, help_text="Hotspot name (e.g., 'hotspot', 'hotspot_lib') - blank for all hotspots")
    order = models.IntegerField(default=0, help_text="Display order (lower numbers shown first)")
    is_active = models.BooleanField(default=True, help_text="Show this card")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_cards')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "Card Content"
        verbose_name_plural = "Card Contents"

    def __str__(self):
        hotspot_info = f" ({self.hotspot_name})" if self.hotspot_name else " (All Hotspots)"
        status = "✓" if self.is_active else "✗"
        return f"{status} {self.title}{hotspot_info}"

    def get_icon_display(self):
        """Return icon image URL if exists, otherwise return emoji"""
        if self.icon_image:
            return self.icon_image.url
        return self.icon


class SystemSettings(models.Model):
    """Model for storing system settings"""
    library_name = models.CharField(max_length=255, default="Library Login System")
    contact_info = models.TextField(blank=True, help_text="Contact information for support")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    default_hotspot_name = models.CharField(max_length=100, blank=True, help_text="Default hotspot name")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"

    def __str__(self):
        return self.library_name
