# apps/dashboard/views/services.py
# from __future__ import annotations
from datetime import timedelta

# --- 1. 클래스에서 사용할 모듈들을 모두 import 합니다. ---
from django.db.models import Sum, F, OuterRef, Subquery
from django.utils import timezone
from ..models import PortfolioHolding, PortfolioSnapshot

class DashboardDataCalculator:
    # --- 2. __init__에서 user_id, asset_type, interval을 파라미터로 받도록 수정 ---
    def __init__(self, user_id: int, asset_type: str = None, interval: str = 'weekly'):
        """
        계산기 초기화
        :param user_id: 사용자 ID
        :param asset_type: 'stock', 'real_estate' 등. None이면 전체 자산을 의미.
        :param interval: 'daily' 또는 'weekly' 같은 기간 선택
        """
        self.user_id = user_id
        self.asset_type = asset_type
        self.interval = interval
        self.today = timezone.now().date() 

        if self.interval == 'daily':
            self.start_date = self.today - timedelta(days=1)
        elif self.interval == 'weekly':
            self.start_date = self.today - timedelta(days=7)
        else: # 기본값
            self.start_date = self.today - timedelta(days=7)
    
    # --- 이하 다른 메서드들은 거의 그대로 사용 가능 ---

    def _get_base_holding_queryset(self):
        """계산의 기본이 되는 자산(Holding) 목록을 가져옵니다."""
        qs = PortfolioHolding.objects.filter(user_id=self.user_id)
        if self.asset_type:
            qs = qs.filter(asset_type=self.asset_type)
        return qs

    def _get_base_snapshot_queryset(self):
        """계산의 기본이 되는 스냅샷 목록을 가져옵니다."""
        qs = PortfolioSnapshot.objects.filter(user_id=self.user_id)
        if self.asset_type:
            qs = qs.filter(asset_type=self.asset_type)
        return qs

    def get_current_total_value(self):
        """1. 현재 총자산 가치를 계산합니다."""
        latest_price_subquery = PortfolioSnapshot.objects.filter(
            user_id=OuterRef('user_id'),
            asset_key=OuterRef('asset_key'),
        ).order_by('-snapshot_date').values('market_price')[:1]

        holdings = self._get_base_holding_queryset().annotate(
            current_price=Subquery(latest_price_subquery)
        ).annotate(
            current_value=F('total_quantity') * F('current_price')
        )
        return holdings.aggregate(total=Sum('current_value'))['total'] or 0

    def get_wow_change_pct(self, current_total_value):
        """2. 주간/일간 변동률을 계산합니다."""
        last_period_value = self._get_base_snapshot_queryset().filter(
            snapshot_date=self.start_date
        ).aggregate(total=Sum('market_value'))['total'] or 0

        if last_period_value > 0:
            return ((current_total_value - last_period_value) / last_period_value) * 100
        return 0

    def get_series_data(self):
        """3. 주간/일간 차트 데이터를 계산합니다."""
        series_data_query = self._get_base_snapshot_queryset().filter(
            snapshot_date__gte=self.start_date
        ).values('snapshot_date').annotate(
            daily_total=Sum('market_value')
        ).order_by('snapshot_date')

        return [
            {"label": item['snapshot_date'].strftime('%a'), "value": item['daily_total']}
            for item in series_data_query
        ]

    def get_data_payload(self):
        """'총자산 카드' 형식의 최종 데이터를 반환합니다."""
        total_value = self.get_current_total_value()
        change_pct = self.get_wow_change_pct(total_value)
        series = self.get_series_data()

        return {
            "total_value": total_value,
            "wow_change_pct": round(change_pct, 2),
            "series": series
        }
