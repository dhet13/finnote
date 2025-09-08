from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('test/', views.test_view, name='test'),
    path('create/', views.create_post_view, name='create_post'),
    path('create/trading/', views.create_trading_post, name='create_trading'),
    path('create/image/', views.create_image_post, name='create_image'),
    path('post/simple/', views.create_simple_post, name='create_simple_post'),
]