from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.db.models import Q
from api.models import BackgroundImage, SystemSettings, TemplateConfig, SlideContent, CardContent, Hotspot, Department
import os
from django.conf import settings as django_settings


def get_user_allowed_hotspots(user):
    """Return list of hotspot_names accessible to user. None means unrestricted (staff)."""
    if user.is_staff:
        return None
    names = Hotspot.objects.filter(
        departments__users=user,
        departments__is_active=True,
        is_active=True
    ).values_list('hotspot_name', flat=True)
    return [n for n in names if n]


def hotspot_filter_q(allowed):
    """Return Q object for filtering content by allowed hotspot_names (plus default/None content)."""
    return Q(hotspot_name__in=allowed) | Q(hotspot_name__isnull=True) | Q(hotspot_name='')


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
    allowed = get_user_allowed_hotspots(request.user)

    if allowed is None:
        image_qs = BackgroundImage.objects.all()
    else:
        image_qs = BackgroundImage.objects.filter(hotspot_filter_q(allowed))

    recent_images = image_qs[:5]
    total_images = image_qs.count()
    active_images = image_qs.filter(is_active=True).count()
    total_users = User.objects.count()

    # Count unique routers visible to user
    hotspot_names = image_qs.exclude(hotspot_name__isnull=True).values_list('hotspot_name', flat=True).distinct()
    total_routers = len(set(hotspot_names))

    # User's departments
    user_departments = request.user.departments.filter(is_active=True) if not request.user.is_staff else None

    context = {
        'recent_images': recent_images,
        'total_images': total_images,
        'active_images': active_images,
        'total_routers': total_routers,
        'total_users': total_users,
        'user_departments': user_departments,
    }
    return render(request, 'webapp/dashboard.html', context)


@login_required
def backgrounds_view(request):
    """Manage background images"""
    allowed = get_user_allowed_hotspots(request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        hotspot_name = request.POST.get('hotspot_name') or None

        # POST guard: block forbidden hotspot
        if allowed is not None and hotspot_name and hotspot_name not in allowed:
            messages.error(request, 'ไม่มีสิทธิ์จัดการ hotspot นี้')
            return redirect('backgrounds')

        if action == 'edit':
            bg_id = request.POST.get('background_id')
            background = get_object_or_404(BackgroundImage, pk=bg_id)

            # Guard: also check the existing record's hotspot
            if allowed is not None and background.hotspot_name and background.hotspot_name not in allowed:
                messages.error(request, 'ไม่มีสิทธิ์จัดการ hotspot นี้')
                return redirect('backgrounds')

            background.title = request.POST.get('title')
            background.hotspot_name = hotspot_name
            background.is_active = request.POST.get('is_active') == 'on'

            new_image = request.FILES.get('image')
            if new_image:
                background.image = new_image

            background.save()
            messages.success(request, f'Background "{background.title}" updated successfully!')
        else:
            title = request.POST.get('title')
            is_active = request.POST.get('is_active') == 'on'
            image = request.FILES.get('image')

            if title and image:
                BackgroundImage.objects.create(
                    title=title,
                    image=image,
                    hotspot_name=hotspot_name,
                    is_active=is_active,
                    uploaded_by=request.user
                )
                messages.success(request, f'Background image "{title}" uploaded successfully!')
            else:
                messages.error(request, 'Please provide both title and image.')

        return redirect('backgrounds')

    if allowed is None:
        backgrounds = BackgroundImage.objects.all().order_by('-uploaded_at')
    else:
        backgrounds = BackgroundImage.objects.filter(hotspot_filter_q(allowed)).order_by('-uploaded_at')

    return render(request, 'webapp/backgrounds.html', {'backgrounds': backgrounds})


@login_required
def set_active_view(request, pk):
    """Set background image as active"""
    if request.method == 'POST':
        background = get_object_or_404(BackgroundImage, pk=pk)
        allowed = get_user_allowed_hotspots(request.user)
        if allowed is not None and background.hotspot_name and background.hotspot_name not in allowed:
            messages.error(request, 'ไม่มีสิทธิ์จัดการ hotspot นี้')
        else:
            background.is_active = True
            background.save()
            messages.success(request, f'Background "{background.title}" is now active.')
    return redirect('backgrounds')


@login_required
def delete_background_view(request, pk):
    """Delete background image"""
    if request.method == 'POST':
        background = get_object_or_404(BackgroundImage, pk=pk)
        allowed = get_user_allowed_hotspots(request.user)
        if allowed is not None and background.hotspot_name and background.hotspot_name not in allowed:
            messages.error(request, 'ไม่มีสิทธิ์จัดการ hotspot นี้')
        else:
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
        organization_name = request.POST.get('organization_name') or ''
        library_name = request.POST.get('library_name')
        contact_info = request.POST.get('contact_info')
        default_hotspot_name = request.POST.get('default_hotspot_name') or ''
        hotspot_status_refresh_interval = int(request.POST.get('hotspot_status_refresh_interval', 10))
        logo = request.FILES.get('logo')

        if settings:
            settings.organization_name = organization_name
            settings.library_name = library_name
            settings.contact_info = contact_info
            settings.default_hotspot_name = default_hotspot_name
            settings.hotspot_status_refresh_interval = hotspot_status_refresh_interval
            settings.updated_by = request.user
            if logo:
                settings.logo = logo
            settings.save()
            messages.success(request, 'Settings updated successfully!')
        else:
            settings = SystemSettings.objects.create(
                organization_name=organization_name,
                library_name=library_name,
                contact_info=contact_info,
                default_hotspot_name=default_hotspot_name,
                hotspot_status_refresh_interval=hotspot_status_refresh_interval,
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
        'hotspot_name': request.GET.get('hotspot_name', ''),

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


def hotspot_login_html(request):
    """Serve hotspot/login.html static file for testing"""
    file_path = os.path.join(django_settings.BASE_DIR, 'hotspot', 'login.html')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html')
    except FileNotFoundError:
        return HttpResponse('Login.html file not found', status=404)


def login_css(request):
    """Serve combined CSS file with cache headers"""
    file_path = os.path.join(django_settings.BASE_DIR, 'static', 'css', 'login.css')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        response = HttpResponse(content, content_type='text/css')
        # Cache for 1 hour (3600 seconds)
        response['Cache-Control'] = 'public, max-age=3600'
        return response
    except FileNotFoundError:
        return HttpResponse('/* CSS file not found */', content_type='text/css', status=404)


# ============================================================================
# Template Management Views
# ============================================================================

@login_required
def templates_view(request):
    """Manage login page templates"""
    allowed = get_user_allowed_hotspots(request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        hotspot_name = request.POST.get('hotspot_name') or None

        # POST guard for create/update
        if action in ('create', 'update'):
            if allowed is not None and hotspot_name and hotspot_name not in allowed:
                messages.error(request, 'ไม่มีสิทธิ์จัดการ hotspot นี้')
                return redirect('templates')

        if action == 'create':
            template_name = request.POST.get('template_name')
            left_panel_component = request.POST.get('left_panel_component')
            is_active = request.POST.get('is_active') == 'on'

            if template_name and left_panel_component:
                TemplateConfig.objects.create(
                    template_name=template_name,
                    left_panel_component=left_panel_component,
                    hotspot_name=hotspot_name,
                    is_active=is_active,
                    created_by=request.user
                )
                messages.success(request, f'Template "{template_name}" created successfully!')
            else:
                messages.error(request, 'Please provide template name and component type.')

        elif action == 'update':
            template_id = request.POST.get('template_id')
            template = get_object_or_404(TemplateConfig, pk=template_id)

            if allowed is not None and template.hotspot_name and template.hotspot_name not in allowed:
                messages.error(request, 'ไม่มีสิทธิ์จัดการ hotspot นี้')
                return redirect('templates')

            template.template_name = request.POST.get('template_name')
            template.left_panel_component = request.POST.get('left_panel_component')
            template.hotspot_name = hotspot_name
            template.is_active = request.POST.get('is_active') == 'on'
            template.save()
            messages.success(request, f'Template "{template.template_name}" updated successfully!')

        elif action == 'delete':
            template_id = request.POST.get('template_id')
            template = get_object_or_404(TemplateConfig, pk=template_id)

            if allowed is not None and template.hotspot_name and template.hotspot_name not in allowed:
                messages.error(request, 'ไม่มีสิทธิ์จัดการ hotspot นี้')
                return redirect('templates')

            template_name = template.template_name
            template.delete()
            messages.success(request, f'Template "{template_name}" deleted successfully!')

        elif action == 'set_active':
            template_id = request.POST.get('template_id')
            template = get_object_or_404(TemplateConfig, pk=template_id)

            if allowed is not None and template.hotspot_name and template.hotspot_name not in allowed:
                messages.error(request, 'ไม่มีสิทธิ์จัดการ hotspot นี้')
                return redirect('templates')

            template.is_active = True
            template.save()
            messages.success(request, f'Template "{template.template_name}" is now active!')

        return redirect('templates')

    # GET request - display templates
    if allowed is None:
        templates = TemplateConfig.objects.all().order_by('-updated_at')
    else:
        templates = TemplateConfig.objects.filter(hotspot_filter_q(allowed)).order_by('-updated_at')

    context = {
        'templates': templates,
        'component_choices': TemplateConfig.COMPONENT_CHOICES,
    }

    return render(request, 'webapp/templates.html', context)


@login_required
def slides_view(request):
    """Manage slide content for slideshow component"""
    allowed = get_user_allowed_hotspots(request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        hotspot_name = request.POST.get('hotspot_name') or None

        if action == 'create':
            if allowed is not None and hotspot_name and hotspot_name not in allowed:
                messages.error(request, 'ไม่มีสิทธิ์จัดการ hotspot นี้')
                return redirect('slides')

            icon = request.POST.get('icon', '')
            icon_image = request.FILES.get('icon_image')
            title = request.POST.get('title')
            description = request.POST.get('description')
            order = request.POST.get('order', 0)
            is_active = request.POST.get('is_active') == 'on'
            show_title = request.POST.get('show_title') == 'on'
            show_description = request.POST.get('show_description') == 'on'
            image_size = request.POST.get('image_size', 'square_400')
            show_link = request.POST.get('show_link') == 'on'
            link_url = request.POST.get('link_url') or None
            link_text = request.POST.get('link_text', 'อ่านต่อ')

            if title and description and (icon or icon_image):
                SlideContent.objects.create(
                    icon=icon,
                    icon_image=icon_image,
                    title=title,
                    description=description,
                    hotspot_name=hotspot_name,
                    order=order,
                    is_active=is_active,
                    show_title=show_title,
                    show_description=show_description,
                    image_size=image_size,
                    show_link=show_link,
                    link_url=link_url,
                    link_text=link_text,
                    created_by=request.user
                )
                messages.success(request, f'Slide "{title}" created successfully!')
            else:
                messages.error(request, 'Please provide title, description, and either icon or image.')

        elif action == 'update':
            slide_id = request.POST.get('slide_id')
            slide = get_object_or_404(SlideContent, pk=slide_id)

            if allowed is not None and slide.hotspot_name and slide.hotspot_name not in allowed:
                messages.error(request, 'ไม่มีสิทธิ์จัดการ hotspot นี้')
                return redirect('slides')
            if allowed is not None and hotspot_name and hotspot_name not in allowed:
                messages.error(request, 'ไม่มีสิทธิ์จัดการ hotspot นี้')
                return redirect('slides')

            slide.icon = request.POST.get('icon', '')
            icon_image = request.FILES.get('icon_image')
            if icon_image:
                slide.icon_image = icon_image

            slide.title = request.POST.get('title')
            slide.description = request.POST.get('description')
            slide.hotspot_name = hotspot_name
            slide.order = request.POST.get('order', 0)
            slide.is_active = request.POST.get('is_active') == 'on'
            slide.show_title = request.POST.get('show_title') == 'on'
            slide.show_description = request.POST.get('show_description') == 'on'
            slide.image_size = request.POST.get('image_size', 'square_400')
            slide.show_link = request.POST.get('show_link') == 'on'
            slide.link_url = request.POST.get('link_url') or None
            slide.link_text = request.POST.get('link_text', 'อ่านต่อ')
            slide.save()
            messages.success(request, f'Slide "{slide.title}" updated successfully!')

        elif action == 'delete':
            slide_id = request.POST.get('slide_id')
            slide = get_object_or_404(SlideContent, pk=slide_id)

            if allowed is not None and slide.hotspot_name and slide.hotspot_name not in allowed:
                messages.error(request, 'ไม่มีสิทธิ์จัดการ hotspot นี้')
                return redirect('slides')

            title = slide.title
            slide.delete()
            messages.success(request, f'Slide "{title}" deleted successfully!')

        return redirect('slides')

    # GET request - display slides
    if allowed is None:
        slides = SlideContent.objects.all().order_by('order', 'created_at')
    else:
        slides = SlideContent.objects.filter(hotspot_filter_q(allowed)).order_by('order', 'created_at')

    context = {
        'slides': slides,
    }

    return render(request, 'webapp/slides.html', context)


@login_required
def cards_view(request):
    """Manage card content for card gallery component"""
    allowed = get_user_allowed_hotspots(request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        hotspot_name = request.POST.get('hotspot_name') or None

        if action == 'create':
            if allowed is not None and hotspot_name and hotspot_name not in allowed:
                messages.error(request, 'ไม่มีสิทธิ์จัดการ hotspot นี้')
                return redirect('cards')

            icon = request.POST.get('icon', '')
            icon_image = request.FILES.get('icon_image')
            title = request.POST.get('title')
            description = request.POST.get('description')
            order = request.POST.get('order', 0)
            is_active = request.POST.get('is_active') == 'on'

            if title and description and (icon or icon_image):
                CardContent.objects.create(
                    icon=icon,
                    icon_image=icon_image,
                    title=title,
                    description=description,
                    hotspot_name=hotspot_name,
                    order=order,
                    is_active=is_active,
                    created_by=request.user
                )
                messages.success(request, f'Card "{title}" created successfully!')
            else:
                messages.error(request, 'Please provide title, description, and either icon or image.')

        elif action == 'update':
            card_id = request.POST.get('card_id')
            card = get_object_or_404(CardContent, pk=card_id)

            if allowed is not None and card.hotspot_name and card.hotspot_name not in allowed:
                messages.error(request, 'ไม่มีสิทธิ์จัดการ hotspot นี้')
                return redirect('cards')
            if allowed is not None and hotspot_name and hotspot_name not in allowed:
                messages.error(request, 'ไม่มีสิทธิ์จัดการ hotspot นี้')
                return redirect('cards')

            card.icon = request.POST.get('icon', '')
            icon_image = request.FILES.get('icon_image')
            if icon_image:
                card.icon_image = icon_image

            card.title = request.POST.get('title')
            card.description = request.POST.get('description')
            card.hotspot_name = hotspot_name
            card.order = request.POST.get('order', 0)
            card.is_active = request.POST.get('is_active') == 'on'
            card.save()
            messages.success(request, f'Card "{card.title}" updated successfully!')

        elif action == 'delete':
            card_id = request.POST.get('card_id')
            card = get_object_or_404(CardContent, pk=card_id)

            if allowed is not None and card.hotspot_name and card.hotspot_name not in allowed:
                messages.error(request, 'ไม่มีสิทธิ์จัดการ hotspot นี้')
                return redirect('cards')

            title = card.title
            card.delete()
            messages.success(request, f'Card "{title}" deleted successfully!')

        return redirect('cards')

    # GET request - display cards
    if allowed is None:
        cards = CardContent.objects.all().order_by('order', 'created_at')
    else:
        cards = CardContent.objects.filter(hotspot_filter_q(allowed)).order_by('order', 'created_at')

    context = {
        'cards': cards,
    }

    return render(request, 'webapp/cards.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def users_view(request):
    """User management (staff only)"""
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
            password2 = request.POST.get('password2', '')
            email = request.POST.get('email', '').strip()
            is_staff = request.POST.get('is_staff') == 'on'
            is_active = request.POST.get('is_active') == 'on'
            department_ids = request.POST.getlist('department_ids')

            if not username or not password:
                messages.error(request, 'Username and password are required.')
            elif password != password2:
                messages.error(request, 'Passwords do not match.')
            elif len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
            elif User.objects.filter(username=username).exists():
                messages.error(request, 'Username already taken.')
            else:
                user = User.objects.create_user(username=username, password=password, email=email)
                user.is_staff = is_staff
                user.is_active = is_active
                user.save()
                for dept in Department.objects.filter(pk__in=department_ids):
                    dept.users.add(user)
                messages.success(request, f'User "{username}" created successfully!')

        elif action == 'edit':
            user_id = request.POST.get('user_id')
            target = get_object_or_404(User, pk=user_id)
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            is_staff = request.POST.get('is_staff') == 'on'
            is_active = request.POST.get('is_active') == 'on'
            department_ids = request.POST.getlist('department_ids')

            if User.objects.filter(username=username).exclude(pk=target.pk).exists():
                messages.error(request, 'Username already taken.')
            elif not is_staff and target.is_staff and User.objects.filter(is_staff=True).count() == 1:
                messages.error(request, 'Cannot remove staff from last admin.')
            else:
                target.username = username
                target.email = email
                target.is_staff = is_staff
                target.is_active = is_active
                target.save()
                # Update department membership: remove from all, then add selected
                for dept in target.departments.all():
                    dept.users.remove(target)
                for dept in Department.objects.filter(pk__in=department_ids):
                    dept.users.add(target)
                messages.success(request, f'User "{username}" updated successfully!')

        elif action == 'change_password':
            user_id = request.POST.get('user_id')
            target = get_object_or_404(User, pk=user_id)
            password = request.POST.get('password', '')
            password2 = request.POST.get('password2', '')

            if password != password2:
                messages.error(request, 'Passwords do not match.')
            elif len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
            else:
                target.set_password(password)
                target.save()
                messages.success(request, f'Password for "{target.username}" changed successfully!')

        elif action == 'delete':
            user_id = request.POST.get('user_id')
            target = get_object_or_404(User, pk=user_id)

            if target == request.user:
                messages.error(request, 'You cannot delete your own account.')
            elif target.is_staff and User.objects.filter(is_staff=True).count() == 1:
                messages.error(request, 'Cannot delete the last admin account.')
            else:
                username = target.username
                target.delete()
                messages.success(request, f'User "{username}" deleted successfully!')

        return redirect('users')

    users = User.objects.all().order_by('username').prefetch_related('departments')
    departments = Department.objects.filter(is_active=True).prefetch_related('hotspots')
    return render(request, 'webapp/users.html', {
        'users': users,
        'departments': departments,
        'staff_count': users.filter(is_staff=True).count(),
        'active_count': users.filter(is_active=True).count(),
    })


@login_required
def hotspots_view(request):
    """Manage hotspot configurations (staff can add/edit/delete; all users can view)"""
    if request.method == 'POST':
        if not request.user.is_staff:
            messages.error(request, 'เฉพาะ Staff เท่านั้นที่สามารถจัดการ Hotspot ได้')
            return redirect('hotspots')

        action = request.POST.get('action')

        if action == 'add':
            hotspot_name = request.POST.get('hotspot_name', '').strip()
            display_name = request.POST.get('display_name', '').strip()
            description = request.POST.get('description', '').strip()
            is_active = request.POST.get('is_active') == 'on'

            if not hotspot_name or not display_name:
                messages.error(request, 'กรุณากรอก Hotspot Name และ Display Name')
            elif Hotspot.objects.filter(hotspot_name=hotspot_name).exists():
                messages.error(request, f'Hotspot Name "{hotspot_name}" มีอยู่แล้ว')
            else:
                Hotspot.objects.create(
                    hotspot_name=hotspot_name,
                    display_name=display_name,
                    description=description,
                    is_active=is_active,
                    created_by=request.user
                )
                messages.success(request, f'เพิ่ม Hotspot "{display_name}" เรียบร้อยแล้ว')

        elif action == 'edit':
            hotspot_id = request.POST.get('hotspot_id')
            hotspot = get_object_or_404(Hotspot, pk=hotspot_id)
            display_name = request.POST.get('display_name', '').strip()
            description = request.POST.get('description', '').strip()
            is_active = request.POST.get('is_active') == 'on'

            if not display_name:
                messages.error(request, 'กรุณากรอก Display Name')
            else:
                hotspot.display_name = display_name
                hotspot.description = description
                hotspot.is_active = is_active
                hotspot.save()
                messages.success(request, f'แก้ไข Hotspot "{display_name}" เรียบร้อยแล้ว')

        elif action == 'delete':
            hotspot_id = request.POST.get('hotspot_id')
            hotspot = get_object_or_404(Hotspot, pk=hotspot_id)
            name = hotspot.display_name
            hotspot.delete()
            messages.success(request, f'ลบ Hotspot "{name}" เรียบร้อยแล้ว')

        return redirect('hotspots')

    hotspots = Hotspot.objects.all().order_by('hotspot_name')
    total = hotspots.count()
    active = hotspots.filter(is_active=True).count()
    ready = sum(1 for h in hotspots if h.status == 'ready')

    return render(request, 'webapp/hotspots.html', {
        'hotspots': hotspots,
        'total': total,
        'active': active,
        'ready': ready,
    })


@login_required
def departments_view(request):
    """Manage departments and their hotspot access"""
    if request.method == 'POST':
        if not request.user.is_staff:
            messages.error(request, 'เฉพาะ Staff เท่านั้นที่สามารถจัดการหน่วยงานได้')
            return redirect('departments')

        action = request.POST.get('action')

        if action == 'add':
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            is_active = request.POST.get('is_active') == 'on'
            hotspot_ids = request.POST.getlist('hotspot_ids')

            if not name:
                messages.error(request, 'กรุณากรอกชื่อหน่วยงาน')
            elif Department.objects.filter(name=name).exists():
                messages.error(request, f'ชื่อหน่วยงาน "{name}" มีอยู่แล้ว')
            else:
                dept = Department.objects.create(
                    name=name,
                    description=description,
                    is_active=is_active,
                    created_by=request.user
                )
                if hotspot_ids:
                    dept.hotspots.set(Hotspot.objects.filter(pk__in=hotspot_ids))
                messages.success(request, f'เพิ่มหน่วยงาน "{name}" เรียบร้อยแล้ว')

        elif action == 'edit':
            dept_id = request.POST.get('dept_id')
            dept = get_object_or_404(Department, pk=dept_id)
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            is_active = request.POST.get('is_active') == 'on'
            hotspot_ids = request.POST.getlist('hotspot_ids')

            if not name:
                messages.error(request, 'กรุณากรอกชื่อหน่วยงาน')
            elif Department.objects.filter(name=name).exclude(pk=dept.pk).exists():
                messages.error(request, f'ชื่อหน่วยงาน "{name}" มีอยู่แล้ว')
            else:
                dept.name = name
                dept.description = description
                dept.is_active = is_active
                dept.save()
                dept.hotspots.set(Hotspot.objects.filter(pk__in=hotspot_ids))
                messages.success(request, f'แก้ไขหน่วยงาน "{name}" เรียบร้อยแล้ว')

        elif action == 'delete':
            dept_id = request.POST.get('dept_id')
            dept = get_object_or_404(Department, pk=dept_id)
            name = dept.name
            dept.delete()
            messages.success(request, f'ลบหน่วยงาน "{name}" เรียบร้อยแล้ว')

        return redirect('departments')

    departments = Department.objects.prefetch_related('hotspots').all()
    hotspots = Hotspot.objects.filter(is_active=True).order_by('display_name')

    context = {
        'departments': departments,
        'hotspots': hotspots,
    }
    return render(request, 'webapp/departments.html', context)


@login_required
def monitoring_view(request):
    """Impression tracking monitoring dashboard"""
    return render(request, 'webapp/monitoring.html')


@login_required
def landing_pages_view(request):
    """Landing page URL management"""
    allowed = get_user_allowed_hotspots(request.user)
    return render(request, 'webapp/landing_pages.html', {'allowed_hotspots': allowed})
