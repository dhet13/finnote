# apps/dashboard/views/services.py
from django.db.models import Sum, Q
from decimal import Decimal
from datetime import datetime, timedelta
from dashboard.models import PortfolioHolding, PortfolioSnapshot


class DashboardDataCalculator:
    """대시보드 데이터 계산 서비스"""
    
    def __init__(self, user_id, asset_type=None, interval='weekly'):
        self.user_id = user_id
        self.asset_type = asset_type
        self.interval = interval
    
    def get_data_payload(self):
        """데이터 페이로드 생성"""
        try:
            # 자산 현황 데이터
            holdings_data = self._get_holdings_data()
            
            # 시계열 데이터
            timeseries_data = self._get_timeseries_data()
            
            return {
                'holdings': holdings_data,
                'timeseries': timeseries_data,
                'status': 'success'
            }
        except Exception as e:
            return {
                'error': str(e),
                'status': 'error'
            }
    
    def _get_holdings_data(self):
        """보유 자산 데이터 조회"""
        # 필터 조건 설정
        filters = {'user_id': self.user_id}
        if self.asset_type:
            filters['asset_type'] = self.asset_type
        
        # 보유 자산 조회
        holdings = PortfolioHolding.objects.filter(**filters)
        
        # 총 투자 금액 계산
        total_invested = holdings.aggregate(
            total=Sum('invested_amount')
        )['total'] or Decimal('0')
        
        # 총 시장 가치 계산 (최신 스냅샷에서)
        latest_snapshots = PortfolioSnapshot.objects.filter(
            user_id=self.user_id,
            **({'asset_type': self.asset_type} if self.asset_type else {})
        ).order_by('-snapshot_date')[:1]
        
        total_market_value = Decimal('0')
        if latest_snapshots.exists():
            total_market_value = latest_snapshots.aggregate(
                total=Sum('market_value')
            )['total'] or Decimal('0')
        
        # 수익률 계산
        if total_invested > 0:
            return_rate = ((total_market_value - total_invested) / total_invested) * 100
        else:
            return_rate = Decimal('0')
        
        return {
            'total_invested': float(total_invested),
            'total_market_value': float(total_market_value),
            'return_rate': float(return_rate),
            'return_amount': float(total_market_value - total_invested),
            'holdings_count': holdings.count()
        }
    
    def _get_timeseries_data(self):
        """시계열 데이터 조회"""
        # 기간 설정
        end_date = datetime.now().date()
        if self.interval == 'daily':
            start_date = end_date - timedelta(days=30)
        elif self.interval == 'weekly':
            start_date = end_date - timedelta(days=90)
        elif self.interval == 'monthly':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)
        
        # 필터 조건
        filters = {
            'user_id': self.user_id,
            'snapshot_date__gte': start_date,
            'snapshot_date__lte': end_date
        }
        if self.asset_type:
            filters['asset_type'] = self.asset_type
        
        # 스냅샷 데이터 조회
        snapshots = PortfolioSnapshot.objects.filter(**filters).order_by('snapshot_date')
        
        # 일별로 그룹화하여 합계 계산
        daily_data = {}
        for snapshot in snapshots:
            date_str = snapshot.snapshot_date.strftime('%Y-%m-%d')
            if date_str not in daily_data:
                daily_data[date_str] = {
                    'date': date_str,
                    'market_value': Decimal('0'),
                    'invested_amount': Decimal('0')
                }
            daily_data[date_str]['market_value'] += snapshot.market_value or Decimal('0')
            daily_data[date_str]['invested_amount'] += snapshot.invested_amount or Decimal('0')
        
        # 시계열 데이터 생성 - 누적 수익률 계산
        timeseries = []
        sorted_dates = sorted(daily_data.keys())
        
        if sorted_dates:
            # 전체 투자금액 기준으로 수익률 계산 (더 정확함)
            total_invested = sum(daily_data[date]['invested_amount'] for date in sorted_dates)
            
            for i, current_date in enumerate(sorted_dates):
                current_data = daily_data[current_date]
                
                # 당일 수익률 계산 (전일 대비)
                if i > 0:
                    prev_data = daily_data[sorted_dates[i-1]]
                    if prev_data['market_value'] > 0:
                        daily_return_rate = ((current_data['market_value'] - prev_data['market_value']) / prev_data['market_value']) * 100
                    else:
                        daily_return_rate = Decimal('0')
                else:
                    daily_return_rate = Decimal('0')
                
                # 누적 수익률 계산 (전체 투자금액 기준)
                if total_invested > 0:
                    cumulative_return_rate = ((current_data['market_value'] - total_invested) / total_invested) * 100
                else:
                    cumulative_return_rate = Decimal('0')
                
                timeseries.append({
                    'date': current_date,
                    'market_value': float(current_data['market_value']),
                    'invested_amount': float(current_data['invested_amount']),
                    'return_rate': float(daily_return_rate),
                    'cumulative_return_rate': float(cumulative_return_rate)
                })
        
        return timeseries


def build_total_card_payload(user_id, interval='weekly'):
    """총자산 카드 데이터 생성"""
    calculator = DashboardDataCalculator(user_id, None, interval)
    return calculator.get_data_payload()


def build_asset_line_payload(user_id, asset_type, interval='weekly'):
    """자산별 라인 차트 데이터 생성"""
    calculator = DashboardDataCalculator(user_id, asset_type, interval)
    return calculator.get_data_payload()


def build_total_timeseries_payload(user_id, interval='weekly'):
    """총자산 시계열 데이터 생성"""
    calculator = DashboardDataCalculator(user_id, None, interval)
    return calculator.get_data_payload()


# DashboardDataCalculator에 필요한 메서드들 추가
def add_portfolio_methods():
    """포트폴리오 관련 메서드들을 DashboardDataCalculator에 추가"""
    
    def get_total_value(self):
        """총 자산 가치 반환"""
        holdings = PortfolioHolding.objects.filter(user_id=self.user_id)
        return float(holdings.aggregate(total=Sum('invested_amount'))['total'] or 0)
    
    def get_total_change(self):
        """총 자산 변화량 반환"""
        snapshots = PortfolioSnapshot.objects.filter(user_id=self.user_id).order_by('-snapshot_date')[:2]
        if len(snapshots) >= 2:
            # market_value 차이로 변화량 계산
            current_value = float(snapshots[0].market_value or 0)
            previous_value = float(snapshots[1].market_value or 0)
            return current_value - previous_value
        return 0.0
    
    def get_total_change_percent(self):
        """총 자산 변화율 반환"""
        snapshots = PortfolioSnapshot.objects.filter(user_id=self.user_id).order_by('-snapshot_date')[:2]
        if len(snapshots) >= 2:
            # market_value 차이로 변화율 계산
            current_value = float(snapshots[0].market_value or 0)
            previous_value = float(snapshots[1].market_value or 0)
            if previous_value > 0:
                return ((current_value - previous_value) / previous_value) * 100
        return 0.0
    
    def get_stock_holdings(self):
        """주식 보유 자산 반환"""
        holdings = PortfolioHolding.objects.filter(user_id=self.user_id, asset_type='stock')
        return [
            {
                'name': h.asset_name,
                'ticker': h.stock_ticker_symbol or '',
                'sector': h.sector_or_region,
                'quantity': float(h.total_quantity),
                'market_value': float(h.invested_amount),
                'currency': h.currency_code
            }
            for h in holdings
        ]
    
    def get_real_estate_holdings(self):
        """부동산 보유 자산 반환"""
        holdings = PortfolioHolding.objects.filter(user_id=self.user_id, asset_type='real_estate')
        return [
            {
                'name': h.asset_name,
                'region': h.sector_or_region,
                'quantity': float(h.total_quantity),
                'market_value': float(h.invested_amount),
                'currency': h.currency_code
            }
            for h in holdings
        ]
    
    def get_sector_breakdown(self):
        """섹터별 분해 반환"""
        holdings = PortfolioHolding.objects.filter(user_id=self.user_id, asset_type='stock')
        sector_data = {}
        
        for holding in holdings:
            sector = holding.sector_or_region
            if sector not in sector_data:
                sector_data[sector] = 0
            sector_data[sector] += float(holding.invested_amount)
        
        return sector_data
    
    def get_region_breakdown(self):
        """지역별 분해 반환"""
        holdings = PortfolioHolding.objects.filter(user_id=self.user_id, asset_type='real_estate')
        region_data = {}
        
        for holding in holdings:
            region = holding.sector_or_region
            if region not in region_data:
                region_data[region] = 0
            region_data[region] += float(holding.invested_amount)
        
        return region_data
    
    def get_timeseries_data(self):
        """시계열 데이터 반환"""
        return self._get_timeseries_data()
    
    # 메서드들을 클래스에 추가
    DashboardDataCalculator.get_total_value = get_total_value
    DashboardDataCalculator.get_total_change = get_total_change
    DashboardDataCalculator.get_total_change_percent = get_total_change_percent
    DashboardDataCalculator.get_stock_holdings = get_stock_holdings
    DashboardDataCalculator.get_real_estate_holdings = get_real_estate_holdings
    DashboardDataCalculator.get_sector_breakdown = get_sector_breakdown
    DashboardDataCalculator.get_region_breakdown = get_region_breakdown
    DashboardDataCalculator.get_timeseries_data = get_timeseries_data

# 메서드들 추가
add_portfolio_methods()