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
    path('create-simple-post/', views.create_simple_post, name='create_simple_post'),
    path('chart-data/', views.get_stock_chart_data, name='chart_data'),
    path('financial-data/', views.get_financial_data, name='financial_data'),
    path('post/<int:post_id>/like/', views.toggle_like, name='toggle_like'),
    path('post/<int:post_id>/bookmark/', views.toggle_bookmark, name='toggle_bookmark'),
    path('post/<int:post_id>/comments/', views.get_comments, name='get_comments'),
    path('post/<int:post_id>/comment/', views.create_comment, name='create_comment'),
    path('post/<int:post_id>/share/', views.toggle_share, name='toggle_share'),
]