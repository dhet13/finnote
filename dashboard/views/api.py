# apps/dashboard/views/api.py
from django.http import JsonResponse, HttpRequest
# from .services import build_total_card_payload, build_asset_line_payload, build_total_timeseries_payload
# from .utils import get_uid, parse_interval, parse_granularity

def api_total(request: HttpRequest) -> JsonResponse:
    """총자산 카드 데이터 API"""
    # 임시 더미 데이터 반환 - 위클리 변동
    return JsonResponse({
        "total_value": 117340,
        "wow_change_pct": 1.74,
        "series": [
            {"label": "Mon", "value": 115000},
            {"label": "Tue", "value": 116200},
            {"label": "Wed", "value": 114800},
            {"label": "Thu", "value": 117000},
            {"label": "Fri", "value": 117340},
            {"label": "Sat", "value": 116900},
            {"label": "Sun", "value": 117100}
        ]
    })

def api_stock(request: HttpRequest) -> JsonResponse:
    """주식 자산 데이터 API"""
    # 임시 더미 데이터 반환 - 주식 자산 변동
    return JsonResponse({
        "total_value": 45000,
        "wow_change_pct": 3.1,
        "series": [
            {"label": "1주전", "value": 42000},
            {"label": "6일전", "value": 42800},
            {"label": "5일전", "value": 43200},
            {"label": "4일전", "value": 43800},
            {"label": "3일전", "value": 44200},
            {"label": "2일전", "value": 44600},
            {"label": "1일전", "value": 45000}
        ]
    })

def api_real_estate(request: HttpRequest) -> JsonResponse:
    """부동산 자산 데이터 API"""
    # 임시 더미 데이터 반환 - 부동산 자산 변동
    return JsonResponse({
        "total_value": 72340,
        "wow_change_pct": 1.5,
        "series": [
            {"label": "1월", "value": 70000},
            {"label": "2월", "value": 70800},
            {"label": "3월", "value": 71200},
            {"label": "4월", "value": 71800},
            {"label": "5월", "value": 72100},
            {"label": "6월", "value": 72340}
        ]
    })

def api_total_timeseries(request: HttpRequest) -> JsonResponse:
    """총자산 시계열 데이터 API"""
    # 임시 더미 데이터 반환
    return JsonResponse({
        "series": [
            {"date": "2024-01", "value": 0.0},
            {"date": "2024-02", "value": 3.2},
            {"date": "2024-03", "value": 5.3},
            {"date": "2024-04", "value": 6.7}
        ]
    })
