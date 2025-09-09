from django.urls import path
from . import views

# This file is included under the /api/ prefix
app_name = 'journals_api'

urlpatterns = [
    path('stock/quote/', views.stock_quote_api, name='stock_quote'),
    path('stock/journals/', views.stock_journals_api, name='stock_journals'),
    path('realty/suggest/', views.realty_suggest_api, name='realty_suggest'),
    path('realty/deals/', views.realty_deals_api, name='realty_deals'),
    path('posts/', views.posts_api, name='posts'),
]
