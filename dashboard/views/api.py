# apps/dashboard/views/api.py
from django.http import JsonResponse, HttpRequest
# from .services import build_total_card_payload, build_asset_line_payload, build_total_timeseries_payload
# from .utils import get_uid, parse_interval, parse_granularity

def api_total(request: HttpRequest) -> JsonResponse:
    """총자산 카드 데이터 API"""
    from .services import DashboardDataCalculator
    
    # URL 파라미터에서 interval 가져오기 (기본값: weekly)
    interval = request.GET.get('interval', 'weekly')
    
    # 사용자 ID 가져오기 (로그인된 사용자)
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        # 실제 데이터 계산기 사용
        calculator = DashboardDataCalculator(
            user_id=request.user.id, 
            asset_type=None,  # 전체 자산
            interval=interval
        )
        data = calculator.get_data_payload()
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def api_stock(request: HttpRequest) -> JsonResponse:
    """주식 자산 데이터 API"""
    from .services import DashboardDataCalculator
    
    interval = request.GET.get('interval', 'weekly')
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        calculator = DashboardDataCalculator(
            user_id=request.user.id, 
            asset_type='stock',  # 주식 자산만
            interval=interval
        )
        data = calculator.get_data_payload()
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def api_real_estate(request: HttpRequest) -> JsonResponse:
    """부동산 자산 데이터 API"""
    from .services import DashboardDataCalculator
    
    interval = request.GET.get('interval', 'weekly')
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        calculator = DashboardDataCalculator(
            user_id=request.user.id, 
            asset_type='real_estate',  # 부동산 자산만
            interval=interval
        )
        data = calculator.get_data_payload()
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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
