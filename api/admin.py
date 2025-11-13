from django.contrib import admin
from django.utils.html import format_html
from .models import BackgroundImage, SystemSettings, SlideContent, TemplateConfig, CardContent


@admin.register(BackgroundImage)
class BackgroundImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'image_preview', 'router_id', 'is_active', 'uploaded_by', 'uploaded_at']
    list_filter = ['is_active', 'router_id', 'uploaded_at']
    search_fields = ['title', 'router_id']
    readonly_fields = ['uploaded_at', 'updated_at', 'image_preview']
    list_editable = ['is_active']

    fieldsets = (
        ('Image Information', {
            'fields': ('title', 'image', 'image_preview', 'router_id')
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
    list_display = ['library_name', 'default_router_id', 'updated_at', 'updated_by']
    readonly_fields = ['updated_at', 'logo_preview']

    fieldsets = (
        ('Library Information', {
            'fields': ('library_name', 'contact_info')
        }),
        ('Branding', {
            'fields': ('logo', 'logo_preview')
        }),
        ('Settings', {
            'fields': ('default_router_id',)
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
    list_display = ['icon', 'title', 'router_id_display', 'order', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'router_id', 'created_at']
    search_fields = ['title', 'description', 'router_id']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'created_at']

    fieldsets = (
        ('Slide Content', {
            'fields': ('icon', 'title', 'description')
        }),
        ('Display Settings', {
            'fields': ('router_id', 'order', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def router_id_display(self, obj):
        return obj.router_id if obj.router_id else "All Routers"
    router_id_display.short_description = 'Router'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TemplateConfig)
class TemplateConfigAdmin(admin.ModelAdmin):
    list_display = ['template_name', 'left_panel_component', 'router_id_display', 'is_active', 'created_by', 'updated_at']
    list_filter = ['left_panel_component', 'is_active', 'router_id', 'created_at']
    search_fields = ['template_name', 'router_id']
    list_editable = ['is_active']
    ordering = ['-updated_at']

    fieldsets = (
        ('Template Information', {
            'fields': ('template_name', 'left_panel_component')
        }),
        ('Assignment', {
            'fields': ('router_id', 'is_active'),
            'description': 'Assign this template to a specific router or leave blank for all routers. Only one template can be active per router.'
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def router_id_display(self, obj):
        return obj.router_id if obj.router_id else "All Routers"
    router_id_display.short_description = 'Router'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CardContent)
class CardContentAdmin(admin.ModelAdmin):
    list_display = ['icon', 'title', 'router_id_display', 'order', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'router_id', 'created_at']
    search_fields = ['title', 'description', 'router_id']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'created_at']

    fieldsets = (
        ('Card Content', {
            'fields': ('icon', 'title', 'description')
        }),
        ('Display Settings', {
            'fields': ('router_id', 'order', 'is_active'),
            'description': 'Cards will be displayed in order from lowest to highest number.'
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def router_id_display(self, obj):
        return obj.router_id if obj.router_id else "All Routers"
    router_id_display.short_description = 'Router'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
