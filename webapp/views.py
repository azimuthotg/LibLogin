from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from api.models import BackgroundImage, SystemSettings


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
