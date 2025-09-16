# apps/dashboard/urls.py
from django.urls import path
from django.shortcuts import redirect

# 페이지 뷰 import
from .views.pages import total_page, portfolio_page, total_content, portfolio_content
# API 뷰 import
from .views.api import api_total, api_stock, api_real_estate, api_total_timeseries, api_portfolio

def dashboard_index(request):
    """대시보드 메인 페이지 - 자산 현황으로 리다이렉트"""
    return redirect('dashboard:page_total')

app_name = "dashboard"
urlpatterns = [
    # 메인 페이지
    path("", dashboard_index, name="dashboard_index"),
    
    # 페이지
    path("total/", total_page, name="page_total"),
    path("portfolio/", portfolio_page, name="page_portfolio"),
    
    # 콘텐츠 전용 (AJAX)
    path("content/total/", total_content, name="content_total"),
    path("content/portfolio/", portfolio_content, name="content_portfolio"),
    
    # API
    path("api/total/", api_total, name="api_total"),
    path("api/stock/", api_stock, name="api_stock"),
    path("api/real_estate/", api_real_estate, name="api_real_estate"),
    path("api/portfolio/", api_portfolio, name="api_portfolio"),
]