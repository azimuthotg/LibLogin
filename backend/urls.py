import time

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from django.db import connection
from django.http import JsonResponse
import os


# Health endpoint สำหรับ NMS Agent monitoring — เช็ก DB ด้วย SELECT 1 (public)
# แยกต่างหากจาก /api/health/ ของแอป (ซึ่งเป็น health ของ API/hotspot คนละเรื่องกัน)
def health(request):
    t0 = time.monotonic()
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        db_status = 'ok'
    except Exception as e:
        db_status = f'error: {e}'
    db_ms = round((time.monotonic() - t0) * 1000)
    status = 'ok' if db_status == 'ok' else 'degraded'
    return JsonResponse(
        {'status': status, 'db': db_status, 'db_ms': db_ms},
        status=200 if status == 'ok' else 503,
    )


urlpatterns = [
    path('health/', health, name='nms_health'),  # NMS monitoring (root-level)
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
