"""
URL configuration for finote project.
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('journals/', include('apps.journals.urls')),
    path('api/', include('apps.journals.api_urls')),
]