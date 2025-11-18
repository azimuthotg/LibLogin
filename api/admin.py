from django.contrib import admin
from django.utils.html import format_html
from .models import BackgroundImage, SystemSettings, SlideContent, TemplateConfig, CardContent, Hotspot


@admin.register(BackgroundImage)
class BackgroundImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'image_preview', 'hotspot_name', 'is_active', 'uploaded_by', 'uploaded_at']
    list_filter = ['is_active', 'hotspot_name', 'uploaded_at']
    search_fields = ['title', 'hotspot_name']
    readonly_fields = ['uploaded_at', 'updated_at', 'image_preview']
    list_editable = ['is_active']

    fieldsets = (
        ('Image Information', {
            'fields': ('title', 'image', 'image_preview', 'hotspot_name')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="150" height="auto" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Hotspot)
class HotspotAdmin(admin.ModelAdmin):
    list_display = ['status_icon_display', 'hotspot_name', 'display_name', 'is_active', 'last_checked_display', 'connection_status']
    list_filter = ['is_active', 'folder_exists', 'login_file_exists', 'config_matched']
    search_fields = ['hotspot_name', 'display_name', 'description']
    list_editable = ['is_active']
    readonly_fields = ['folder_exists', 'login_file_exists', 'config_matched', 'last_checked', 'created_at', 'updated_at', 'status_display']

    fieldsets = (
        ('Hotspot Information', {
            'fields': ('hotspot_name', 'display_name', 'description', 'is_active')
        }),
        ('Connection Status', {
            'fields': ('status_display', 'folder_exists', 'login_file_exists', 'config_matched', 'last_checked'),
            'description': 'Connection status is updated when you test the hotspot connection via the API or management interface.'
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_icon_display(self, obj):
        return obj.status_icon
    status_icon_display.short_description = ''

    def connection_status(self, obj):
        status_colors = {
            'ready': 'green',
            'warning': 'orange',
            'error': 'red',
            'unchecked': 'gray'
        }
        color = status_colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.status.upper()
        )
    connection_status.short_description = 'Status'

    def last_checked_display(self, obj):
        if obj.last_checked:
            return obj.last_checked.strftime('%Y-%m-%d %H:%M')
        return 'Never'
    last_checked_display.short_description = 'Last Checked'

    def status_display(self, obj):
        if not obj.last_checked:
            return format_html('<p style="color: gray;">⚪ Not tested yet. Use API to test connection.</p>')

        status_html = f'<p><strong>Status:</strong> {obj.status_icon} {obj.status.upper()}</p><ul>'
        status_html += f'<li>Folder exists: {"✓" if obj.folder_exists else "✗"}</li>'
        status_html += f'<li>login.html exists: {"✓" if obj.login_file_exists else "✗"}</li>'
        status_html += f'<li>Config matched: {"✓" if obj.config_matched else "✗"}</li>'
        status_html += '</ul>'
        return format_html(status_html)
    status_display.short_description = 'Connection Details'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['organization_name', 'library_name', 'default_hotspot_name', 'hotspot_status_refresh_interval', 'updated_at', 'updated_by']
    readonly_fields = ['updated_at', 'logo_preview']

    fieldsets = (
        ('Organization Information', {
            'fields': ('organization_name',)
        }),
        ('Library Information', {
            'fields': ('library_name', 'contact_info')
        }),
        ('Branding', {
            'fields': ('logo', 'logo_preview')
        }),
        ('Hotspot Settings', {
            'fields': ('default_hotspot_name', 'hotspot_status_refresh_interval')
        }),
        ('Metadata', {
            'fields': ('updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="150" height="auto" />', obj.logo.url)
        return "No Logo"
    logo_preview.short_description = 'Logo Preview'

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SlideContent)
class SlideContentAdmin(admin.ModelAdmin):
    list_display = ['icon', 'title', 'hotspot_name_display', 'order', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'hotspot_name', 'created_at']
    search_fields = ['title', 'description', 'hotspot_name']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'created_at']

    fieldsets = (
        ('Slide Content', {
            'fields': ('icon', 'title', 'description')
        }),
        ('Display Settings', {
            'fields': ('hotspot_name', 'order', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def hotspot_name_display(self, obj):
        return obj.hotspot_name if obj.hotspot_name else "All Hotspots"
    hotspot_name_display.short_description = 'Hotspot'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TemplateConfig)
class TemplateConfigAdmin(admin.ModelAdmin):
    list_display = ['template_name', 'left_panel_component', 'hotspot_name_display', 'is_active', 'created_by', 'updated_at']
    list_filter = ['left_panel_component', 'is_active', 'hotspot_name', 'created_at']
    search_fields = ['template_name', 'hotspot_name']
    list_editable = ['is_active']
    ordering = ['-updated_at']

    fieldsets = (
        ('Template Information', {
            'fields': ('template_name', 'left_panel_component')
        }),
        ('Assignment', {
            'fields': ('hotspot_name', 'is_active'),
            'description': 'Assign this template to a specific hotspot or leave blank for all hotspots. Only one template can be active per hotspot.'
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def hotspot_name_display(self, obj):
        return obj.hotspot_name if obj.hotspot_name else "All Hotspots"
    hotspot_name_display.short_description = 'Hotspot'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CardContent)
class CardContentAdmin(admin.ModelAdmin):
    list_display = ['icon', 'title', 'hotspot_name_display', 'order', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'hotspot_name', 'created_at']
    search_fields = ['title', 'description', 'hotspot_name']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'created_at']

    fieldsets = (
        ('Card Content', {
            'fields': ('icon', 'title', 'description')
        }),
        ('Display Settings', {
            'fields': ('hotspot_name', 'order', 'is_active'),
            'description': 'Cards will be displayed in order from lowest to highest number.'
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def hotspot_name_display(self, obj):
        return obj.hotspot_name if obj.hotspot_name else "All Hotspots"
    hotspot_name_display.short_description = 'Hotspot'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
