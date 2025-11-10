from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('backgrounds/', views.backgrounds_view, name='backgrounds'),
    path('backgrounds/<int:pk>/set-active/', views.set_active_view, name='set_active'),
    path('backgrounds/<int:pk>/delete/', views.delete_background_view, name='delete_background'),
    path('settings/', views.settings_view, name='settings'),
]
