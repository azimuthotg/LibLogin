from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from api.models import BackgroundImage, SystemSettings
import os
from django.conf import settings as django_settings


def login_view(request):
    """Login page for librarians and admins"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'webapp/login.html')


@login_required
def logout_view(request):
    """Logout user"""
    auth_logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def dashboard_view(request):
    """Dashboard showing overview"""
    recent_images = BackgroundImage.objects.all()[:5]
    total_images = BackgroundImage.objects.count()
    active_images = BackgroundImage.objects.filter(is_active=True).count()
    total_users = User.objects.count()

    # Count unique routers
    router_ids = BackgroundImage.objects.exclude(router_id__isnull=True).values_list('router_id', flat=True).distinct()
    total_routers = len(set(router_ids))

    context = {
        'recent_images': recent_images,
        'total_images': total_images,
        'active_images': active_images,
        'total_routers': total_routers,
        'total_users': total_users,
    }
    return render(request, 'webapp/dashboard.html', context)


@login_required
def backgrounds_view(request):
    """Manage background images"""
    if request.method == 'POST':
        # Handle image upload
        title = request.POST.get('title')
        router_id = request.POST.get('router_id') or None
        is_active = request.POST.get('is_active') == 'on'
        image = request.FILES.get('image')

        if title and image:
            background = BackgroundImage.objects.create(
                title=title,
                image=image,
                router_id=router_id,
                is_active=is_active,
                uploaded_by=request.user
            )
            messages.success(request, f'Background image "{title}" uploaded successfully!')
        else:
            messages.error(request, 'Please provide both title and image.')

        return redirect('backgrounds')

    backgrounds = BackgroundImage.objects.all().order_by('-uploaded_at')
    return render(request, 'webapp/backgrounds.html', {'backgrounds': backgrounds})


@login_required
def set_active_view(request, pk):
    """Set background image as active"""
    if request.method == 'POST':
        background = get_object_or_404(BackgroundImage, pk=pk)
        background.is_active = True
        background.save()
        messages.success(request, f'Background "{background.title}" is now active.')
    return redirect('backgrounds')


@login_required
def delete_background_view(request, pk):
    """Delete background image"""
    if request.method == 'POST':
        background = get_object_or_404(BackgroundImage, pk=pk)
        title = background.title
        background.delete()
        messages.success(request, f'Background "{title}" deleted successfully.')
    return redirect('backgrounds')


@login_required
@user_passes_test(lambda u: u.is_staff)
def settings_view(request):
    """System settings (admin only)"""
    # Get or create settings
    settings = SystemSettings.objects.first()

    if request.method == 'POST':
        library_name = request.POST.get('library_name')
        contact_info = request.POST.get('contact_info')
        default_router_id = request.POST.get('default_router_id') or ''
        logo = request.FILES.get('logo')

        if settings:
            settings.library_name = library_name
            settings.contact_info = contact_info
            settings.default_router_id = default_router_id
            settings.updated_by = request.user
            if logo:
                settings.logo = logo
            settings.save()
            messages.success(request, 'Settings updated successfully!')
        else:
            settings = SystemSettings.objects.create(
                library_name=library_name,
                contact_info=contact_info,
                default_router_id=default_router_id,
                logo=logo if logo else None,
                updated_by=request.user
            )
            messages.success(request, 'Settings created successfully!')

        return redirect('settings')

    total_images = BackgroundImage.objects.count()
    total_users = User.objects.count()

    context = {
        'settings': settings,
        'total_images': total_images,
        'total_users': total_users,
    }
    return render(request, 'webapp/settings.html', context)


# ============================================================================
# MikroTik Hotspot Views (Public - No Authentication Required)
# ============================================================================

@csrf_exempt
def hotspot_login(request):
    """
    Hotspot Login Page for MikroTik
    URL: /hotspot/login/
    Receives parameters from MikroTik and displays login page
    """
    # Get system settings
    settings = SystemSettings.objects.first()

    # Get MikroTik parameters
    context = {
        'link_login': request.GET.get('link-login', ''),
        'link_login_only': request.GET.get('link-login-only', ''),
        'link_orig': request.GET.get('link-orig', 'http://www.google.com'),
        'mac': request.GET.get('mac', ''),
        'ip': request.GET.get('ip', ''),
        'username': request.GET.get('username', ''),
        'error': request.GET.get('error', ''),
        'trial': request.GET.get('trial', ''),
        'chap_id': request.GET.get('chap-id', ''),
        'chap_challenge': request.GET.get('chap-challenge', ''),
        'popup': request.GET.get('popup', 'false'),
        'router_id': request.GET.get('router_id', ''),

        # System settings
        'library_name': settings.library_name if settings else 'Library WiFi System',
        'contact_info': settings.contact_info if settings else '',
        'logo_url': settings.logo.url if settings and settings.logo else None,
    }

    return render(request, 'webapp/hotspot_login.html', context)


@csrf_exempt
def hotspot_logout(request):
    """
    Hotspot Logout Page
    URL: /hotspot/logout/
    Shows logout success message and redirects
    """
    settings = SystemSettings.objects.first()

    context = {
        'link_status': request.GET.get('link-status', ''),
        'link_orig': request.GET.get('link-orig', ''),
        'mac': request.GET.get('mac', ''),
        'ip': request.GET.get('ip', ''),
        'username': request.GET.get('username', ''),
        'logout_id': request.GET.get('logout-id', ''),
        'erase_cookie': request.GET.get('erase-cookie', 'false'),

        # System settings
        'library_name': settings.library_name if settings else 'Library WiFi System',
        'contact_info': settings.contact_info if settings else '',
        'logo_url': settings.logo.url if settings and settings.logo else None,
    }

    return render(request, 'webapp/hotspot_logout.html', context)


@csrf_exempt
def hotspot_status(request):
    """
    Hotspot Status Page
    URL: /hotspot/status/
    Shows connection status and usage information
    """
    settings = SystemSettings.objects.first()

    context = {
        'link_status': request.GET.get('link-status', ''),
        'link_logout': request.GET.get('link-logout', ''),
        'link_orig': request.GET.get('link-orig', ''),
        'mac': request.GET.get('mac', ''),
        'ip': request.GET.get('ip', ''),
        'username': request.GET.get('username', ''),
        'uptime': request.GET.get('uptime', '0'),
        'session_time_left': request.GET.get('session-time-left', '0'),
        'bytes_in': request.GET.get('bytes-in', '0'),
        'bytes_out': request.GET.get('bytes-out', '0'),
        'refresh_timeout': request.GET.get('refresh-timeout', '30'),

        # System settings
        'library_name': settings.library_name if settings else 'Library WiFi System',
        'contact_info': settings.contact_info if settings else '',
        'logo_url': settings.logo.url if settings and settings.logo else None,
    }

    return render(request, 'webapp/hotspot_status.html', context)


@csrf_exempt
def hotspot_error(request):
    """
    Hotspot Error Page
    URL: /hotspot/error/
    Shows error messages from MikroTik
    """
    settings = SystemSettings.objects.first()

    context = {
        'error': request.GET.get('error', 'Unknown error occurred'),
        'link_status': request.GET.get('link-status', ''),
        'link_login': request.GET.get('link-login', ''),

        # System settings
        'library_name': settings.library_name if settings else 'Library WiFi System',
        'contact_info': settings.contact_info if settings else '',
        'logo_url': settings.logo.url if settings and settings.logo else None,
    }

    return render(request, 'webapp/hotspot_error.html', context)


def test_hotspot_background(request):
    """Serve test_hotspot_background.html static file"""
    file_path = os.path.join(django_settings.BASE_DIR, 'test_hotspot_background.html')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html')
    except FileNotFoundError:
        return HttpResponse('Test file not found', status=404)
