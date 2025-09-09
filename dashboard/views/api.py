# apps/dashboard/views/api.py
from django.http import JsonResponse, HttpRequest

def api_total(request: HttpRequest) -> JsonResponse:
    """총자산 카드 데이터 API"""
    # 임시 더미 데이터
    return JsonResponse({
        "total_value": 1000000,
        "wow_change_pct": 5.2,
        "series": [
            {"label": "2024-01", "value": 950000},
            {"label": "2024-02", "value": 980000},
            {"label": "2024-03", "value": 1000000}
        ]
    })

def api_stock(request: HttpRequest) -> JsonResponse:
    """주식 차트 데이터 API"""
    # 임시 더미 데이터
    return JsonResponse({
        "latest_change_pct": 3.1,
        "series": [
            {"label": "2024-01", "value": 2.1},
            {"label": "2024-02", "value": 1.8},
            {"label": "2024-03", "value": 3.1}
        ]
    })

def api_real_estate(request: HttpRequest) -> JsonResponse:
    """부동산 차트 데이터 API"""
    # 임시 더미 데이터
    return JsonResponse({
        "latest_change_pct": 1.5,
        "series": [
            {"label": "2024-01", "value": 0.8},
            {"label": "2024-02", "value": 1.2},
            {"label": "2024-03", "value": 1.5}
        ]
    })

def api_total_timeseries(request: HttpRequest) -> JsonResponse:
    """총자산 시계열 데이터 API"""
    # 임시 더미 데이터
    return JsonResponse({
        "series": [
            {"date": "2024-01", "value": 0.0},
            {"date": "2024-02", "value": 3.2},
            {"date": "2024-03", "value": 5.3}
        ]
    })
