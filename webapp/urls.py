from django.urls import path
from . import views

urlpatterns = [
    # Admin/Librarian Interface
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('backgrounds/', views.backgrounds_view, name='backgrounds'),
    path('backgrounds/<int:pk>/set-active/', views.set_active_view, name='set_active'),
    path('backgrounds/<int:pk>/delete/', views.delete_background_view, name='delete_background'),
    path('settings/', views.settings_view, name='settings'),

    # MikroTik Hotspot Pages (Public)
    path('hotspot/login/', views.hotspot_login, name='hotspot_login'),
    path('hotspot/logout/', views.hotspot_logout, name='hotspot_logout'),
    path('hotspot/status/', views.hotspot_status, name='hotspot_status'),
    path('hotspot/error/', views.hotspot_error, name='hotspot_error'),

    # Test Pages
    path('test_hotspot_background.html', views.test_hotspot_background, name='test_hotspot_background'),
    path('hotspot/login.html', views.hotspot_login_html, name='hotspot_login_html'),
]
