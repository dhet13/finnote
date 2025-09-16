# user_profile/urls.py
from django.urls import path
from . import views

app_name = 'user_profile'
1
urlpatterns = [
    path('my-posts/', views.my_posts_view, name='my_posts'),
    path('liked-posts/', views.liked_posts_view, name='liked_posts'),
    path('bookmarked-posts/', views.bookmarked_posts_view, name='bookmarked_posts'),
    path('profile', views.my_profile, name='user_profile'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('add_asset/', views.add_stock_asset, name='add_stock_asset'),
    path('delete_stock/<str:my_ID>/<str:ticker_symbol>/', views.delete_stock_asset, name='delete_stock_asset'),
    path('delete_real_estate/<int:deal_id>/', views.delete_real_estate_asset, name='delete_real_estate_asset'),
    path('likes',views.user_likes_view,name='user_likes'),
    path('add_real_estate_asset/', views.add_real_estate_asset, name='add_real_estate_asset'),
    path('<str:my_ID>/', views.user_profile, name='profile'),
    
]