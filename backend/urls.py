from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', include('webapp.urls')),
]

# Serve media and static files via Waitress (works with DEBUG=False)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]

# Serve hotspot login pages from multiple hotspot folders
def serve_hotspot_file(request, hotspot_name, path):
    document_root = os.path.join(settings.BASE_DIR, hotspot_name)
    return serve(request, path, document_root=document_root)

urlpatterns += [
    re_path(r'^(hotspot[^/]*)/(.*)$', serve_hotspot_file, name='hotspot_files'),
]
