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
    from .services import build_total_timeseries_payload
    
    interval = request.GET.get('interval', 'weekly')
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        data = build_total_timeseries_payload(request.user.id, interval)
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def api_portfolio(request: HttpRequest) -> JsonResponse:
    """포트폴리오 데이터 API"""
    from .services import DashboardDataCalculator
    
    interval = request.GET.get('interval', 'weekly')
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        # 포트폴리오 데이터 계산
        calculator = DashboardDataCalculator(
            user_id=request.user.id, 
            asset_type=None,  # 전체 자산
            interval=interval
        )
        
        # 포트폴리오 전용 데이터 구조
        stock_holdings = calculator.get_stock_holdings()
        real_estate_holdings = calculator.get_real_estate_holdings()
        
        print(f"=== 포트폴리오 API 디버깅 ===")
        print(f"stock_holdings 개수: {len(stock_holdings) if stock_holdings else 0}")
        print(f"real_estate_holdings 개수: {len(real_estate_holdings) if real_estate_holdings else 0}")
        print(f"stock_holdings 내용: {stock_holdings}")
        print(f"real_estate_holdings 내용: {real_estate_holdings}")
        
        data = {
            'total_value': calculator.get_total_value(),
            'total_change': calculator.get_total_change(),
            'total_change_percent': calculator.get_total_change_percent(),
            'stock_holdings': stock_holdings,
            'real_estate_holdings': real_estate_holdings,
            'sector_breakdown': calculator.get_sector_breakdown(),
            'region_breakdown': calculator.get_region_breakdown(),
            'timeseries_data': calculator.get_timeseries_data(),
            'recent_journal_entries': calculator.get_recent_journal_entries(),
            'journal_statistics': calculator.get_journal_statistics()
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def api_journal_entries(request: HttpRequest) -> JsonResponse:
    """매매일지 데이터 API"""
    from .services import DashboardDataCalculator
    
    limit = int(request.GET.get('limit', 10))
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        calculator = DashboardDataCalculator(
            user_id=request.user.id, 
            asset_type=None,
            interval='weekly'
        )
        
        data = {
            'recent_entries': calculator.get_recent_journal_entries(limit),
            'statistics': calculator.get_journal_statistics()
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
