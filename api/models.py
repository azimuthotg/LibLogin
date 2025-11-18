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


class Hotspot(models.Model):
    """Model for managing hotspot configurations and status"""
    hotspot_name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Technical hotspot name (e.g., 'hotspot', 'hotspot_lab', 'hotspot_office')"
    )
    display_name = models.CharField(
        max_length=100,
        help_text="Friendly display name (e.g., 'Default Hotspot', 'Laboratory')"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of this hotspot location/purpose"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this hotspot currently in use?"
    )

    # Connection status fields (updated by test_connection)
    folder_exists = models.BooleanField(
        default=False,
        help_text="Does the hotspot_xxx folder exist?"
    )
    login_file_exists = models.BooleanField(
        default=False,
        help_text="Does login.html file exist in the folder?"
    )
    config_matched = models.BooleanField(
        default=False,
        help_text="Does window.HOTSPOT_NAME match the hotspot_name?"
    )
    last_checked = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time connection was tested"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_hotspots'
    )

    class Meta:
        ordering = ['hotspot_name']
        verbose_name = "Hotspot"
        verbose_name_plural = "Hotspots"

    def __str__(self):
        return f"{self.display_name} ({self.hotspot_name})"

    @property
    def status(self):
        """Return connection status: ready, warning, error, or unchecked"""
        if not self.last_checked:
            return 'unchecked'
        if self.folder_exists and self.login_file_exists and self.config_matched:
            return 'ready'
        elif self.folder_exists:
            return 'warning'
        return 'error'

    @property
    def status_icon(self):
        """Return status icon emoji"""
        status_icons = {
            'ready': '🟢',
            'warning': '🟡',
            'error': '🔴',
            'unchecked': '⚪'
        }
        return status_icons.get(self.status, '⚪')

    def delete(self, *args, **kwargs):
        """Override delete to cascade delete related content"""
        # Delete related templates
        TemplateConfig.objects.filter(hotspot_name=self.hotspot_name).delete()
        # Delete related backgrounds
        BackgroundImage.objects.filter(hotspot_name=self.hotspot_name).delete()
        # Delete related slides
        SlideContent.objects.filter(hotspot_name=self.hotspot_name).delete()
        # Delete related cards
        CardContent.objects.filter(hotspot_name=self.hotspot_name).delete()
        # Delete the hotspot itself
        super().delete(*args, **kwargs)


class SystemSettings(models.Model):
    """Model for storing system settings"""
    REFRESH_INTERVAL_CHOICES = [
        (5, '5 minutes'),
        (10, '10 minutes'),
        (15, '15 minutes'),
        (30, '30 minutes'),
        (60, '60 minutes'),
    ]

    organization_name = models.CharField(max_length=255, blank=True, help_text="Organization name (e.g., University, Library)")
    library_name = models.CharField(max_length=255, default="Library Login System")
    contact_info = models.TextField(blank=True, help_text="Contact information for support")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    default_hotspot_name = models.CharField(max_length=100, blank=True, help_text="Default hotspot name")
    hotspot_status_refresh_interval = models.IntegerField(
        choices=REFRESH_INTERVAL_CHOICES,
        default=10,
        help_text="Auto-refresh interval for hotspot status (in minutes)"
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"

    def __str__(self):
        return self.library_name


class PageImpression(models.Model):
    """Log every time someone views the login page (Impression/Reach tracking)"""

    # Core data
    hotspot_name = models.CharField(max_length=100, db_index=True, help_text="Hotspot identifier")
    viewed_at = models.DateTimeField(auto_now_add=True, db_index=True, help_text="When page was viewed")

    # Device identification (for unique counting)
    mac_hash = models.CharField(max_length=64, db_index=True, help_text="SHA256 hash of MAC address")
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address assigned")

    # Device info
    device_type = models.CharField(max_length=20, null=True, blank=True, help_text="mobile/desktop/tablet")
    user_agent = models.TextField(null=True, blank=True, help_text="Browser user agent string")

    # Engagement metrics
    time_on_page = models.IntegerField(null=True, blank=True, help_text="Seconds spent on page")

    # Metadata
    is_unique_today = models.BooleanField(default=True, help_text="First impression from this device today")

    class Meta:
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['hotspot_name', 'viewed_at']),
            models.Index(fields=['mac_hash', 'viewed_at']),
            models.Index(fields=['hotspot_name', 'mac_hash', 'viewed_at']),
        ]
        verbose_name = "Page Impression"
        verbose_name_plural = "Page Impressions"

    def __str__(self):
        return f"{self.hotspot_name} - {self.viewed_at.strftime('%Y-%m-%d %H:%M')}"


class DailyReachStats(models.Model):
    """Aggregated daily reach statistics per hotspot"""

    hotspot_name = models.CharField(max_length=100, db_index=True)
    date = models.DateField(db_index=True)

    # Reach metrics
    total_impressions = models.IntegerField(default=0, help_text="Total page views")
    unique_devices = models.IntegerField(default=0, help_text="Unique MAC addresses")

    # Device breakdown
    mobile_count = models.IntegerField(default=0)
    desktop_count = models.IntegerField(default=0)
    tablet_count = models.IntegerField(default=0)
    unknown_count = models.IntegerField(default=0)

    # Engagement metrics
    avg_time_on_page = models.FloatField(default=0.0, help_text="Average seconds on page")
    total_time_on_page = models.IntegerField(default=0, help_text="Total seconds across all impressions")

    # Hourly breakdown (JSON field for charts)
    hourly_data = models.JSONField(default=dict, null=True, blank=True, help_text="Hourly impression counts {hour: count}")

    # Metadata
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['hotspot_name', 'date']
        ordering = ['-date', 'hotspot_name']
        verbose_name = "Daily Reach Statistics"
        verbose_name_plural = "Daily Reach Statistics"
        indexes = [
            models.Index(fields=['date', 'hotspot_name']),
            models.Index(fields=['hotspot_name', 'date']),
        ]

    def __str__(self):
        return f"{self.hotspot_name} - {self.date} ({self.unique_devices} unique, {self.total_impressions} total)"


class LandingPageURL(models.Model):
    """Landing page URL for post-login redirect (per hotspot)"""

    title = models.CharField(max_length=255, help_text="Description (e.g., Library Portal, Promotion Page)")
    url = models.URLField(max_length=500, help_text="Redirect URL after successful login")
    hotspot_name = models.CharField(max_length=100, db_index=True, help_text="Hotspot identifier")
    is_active = models.BooleanField(default=False, help_text="Active redirect for this hotspot")

    # Analytics
    redirect_count = models.IntegerField(default=0, help_text="Number of times users were redirected")
    last_redirected_at = models.DateTimeField(null=True, blank=True, help_text="Last redirect timestamp")

    # Optional priority for future A/B testing
    priority = models.IntegerField(default=0, help_text="Priority (higher = preferred if multiple active)")

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='landing_urls')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Landing Page URL"
        verbose_name_plural = "Landing Page URLs"
        ordering = ['-is_active', '-priority', '-created_at']
        indexes = [
            models.Index(fields=['hotspot_name', 'is_active']),
            models.Index(fields=['is_active', 'hotspot_name']),
        ]

    def __str__(self):
        status = "🟢 Active" if self.is_active else "⚪ Inactive"
        return f"{status} | {self.title} ({self.hotspot_name})"

    def increment_redirect_count(self):
        """Increment redirect counter and update timestamp"""
        from django.utils import timezone
        self.redirect_count += 1
        self.last_redirected_at = timezone.now()
        self.save(update_fields=['redirect_count', 'last_redirected_at'])
