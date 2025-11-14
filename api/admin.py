from django.contrib import admin
from django.utils.html import format_html
from .models import BackgroundImage, SystemSettings, SlideContent, TemplateConfig, CardContent


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


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['library_name', 'default_hotspot_name', 'updated_at', 'updated_by']
    readonly_fields = ['updated_at', 'logo_preview']

    fieldsets = (
        ('Library Information', {
            'fields': ('library_name', 'contact_info')
        }),
        ('Branding', {
            'fields': ('logo', 'logo_preview')
        }),
        ('Settings', {
            'fields': ('default_hotspot_name',)
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
