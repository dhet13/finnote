# user_profile/urls.py
from django.urls import path
from . import views

app_name = 'user_profile'

urlpatterns = [
    path('profile', views.my_profile, name='user_profile'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('add_asset/', views.add_stock_asset, name='add_stock_asset'),
    path('<str:my_ID>/', views.user_profile, name='profile'),
    path('likes',views.user_likes_view,name='user_likes')
    
]