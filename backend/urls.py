"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', include('webapp.urls')),  # Frontend webapp
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')

    # Serve hotspot login pages from multiple hotspot folders
    # Pattern matches: /hotspot/, /hotspot_lib/, /hotspot_building3/, etc.
    from django.views.static import serve
    from django.urls import re_path
    import os

    def serve_hotspot_file(request, hotspot_name, path):
        """Serve files from hotspot folders"""
        document_root = os.path.join(settings.BASE_DIR, hotspot_name)
        return serve(request, path, document_root=document_root)

    urlpatterns += [
        re_path(r'^(hotspot[^/]*)/(.*)$', serve_hotspot_file, name='hotspot_files'),
    ]
