# user_profile/urls.py
from django.urls import path
from . import views

app_name = 'user_profile'

urlpatterns = [
    path('profile', views.my_profile, name='user_profile'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('<str:my_ID>/', views.user_profile, name='profile'),
    
]