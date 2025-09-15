from django.urls import path
from . import views

app_name = 'journals'

urlpatterns = [
    path('compose/', views.compose, name='compose'),
    path('my-list/', views.my_journal_list, name='my_list'),
    path('stock/<int:pk>/', views.stock_detail_view, name='stock_detail'),
    path('stock/summary/<str:ticker_symbol>/', views.stock_summary_detail, name='stock_summary_detail'), # New path for aggregated stock view
    # path('realty/<int:pk>/', views.realty_detail, name='realty_detail'), # realty_detail 뷰 함수가 없어 임시 주석 처리
]
