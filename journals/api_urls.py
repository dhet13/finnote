from django.urls import path
from . import views

# This file is included under the /api/ prefix
app_name = 'journals_api'

urlpatterns = [
    path('stock/search/', views.stock_search_api, name='stock_search'),
    path('stock/portfolio-summary/', views.portfolio_summary_api, name='portfolio_summary'),
    path('stock/<str:ticker>/card-details/', views.stock_card_details_api, name='stock_card_details'),
    path('stock/quote/', views.stock_quote_api, name='stock_quote'),
    path('stock/<str:ticker>/history/', views.stock_history_api, name='stock_history'),
    path('stock/journals/', views.stock_journals_api, name='stock_journals'),
    path('stock/journals/<int:journal_id>/trades/', views.add_stock_trade_api, name='add_stock_trade'),
    path('realty/suggest/', views.realty_suggest_api, name='realty_suggest'),
    path('realty/deals/', views.realty_deals_api, name='realty_deals'),
    path('journal-posts/<int:post_id>/', views.journal_post_api, name='journal_post_api'),
    path('posts/', views.posts_api, name='posts'),
]