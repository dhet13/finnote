# apps/dashboard/urls.py
from django.urls import path

# 페이지 뷰 import
from .views.pages import total_page
# API 뷰 import
from .views.api import api_total, api_stock, api_real_estate, api_total_timeseries

app_name = "dashboard"
urlpatterns = [
    # 페이지
    path("total/", total_page, name="page_total"),
    path("portfolio/", total_page, name="page_portfolio"),  # 일단 같은 뷰로 렌더링만(임시)
    
    # API
    path("api/total", api_total, name="api_total"),
    path("api/stock", api_stock, name="api_stock"),
    path("api/real_estate", api_real_estate, name="api_real_estate"),
    path("api/total/timeseries", api_total_timeseries, name="api_total_timeseries"),
]