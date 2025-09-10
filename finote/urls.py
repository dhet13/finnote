"""
URL configuration for finote project.
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    
    # 앱별 URL 연결
    path('dashboard/', include('dashboard.urls')),
    path('home/', include('home.urls')),
    path('accounts/', include('accounts.urls')),
    path('profile/', include('user_profile.urls')),
    path('base/', include('base.urls')),
    path('journals/', include('journals.urls')),
    path('api/', include('journals.api_urls')),
]