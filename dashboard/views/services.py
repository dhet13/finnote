# apps/dashboard/views/services.py
from django.db.models import Sum, Q
from decimal import Decimal
from datetime import datetime, timedelta
<<<<<<< HEAD
from dashboard.models import PortfolioHolding, PortfolioSnapshot
=======
from dashboard.models import PortfolioHolding, PortfolioSnapshot, AssetLogUnified
from journals.models import StockJournal, StockInfo, StockTrade
>>>>>>> d8922d3 (전체적인 파일 수정)
import requests
import yfinance as yf


class CurrencyConverter:
    """통화 변환 클래스"""
    
    @staticmethod
    def get_usd_to_krw_rate():
        """USD to KRW 환율 조회"""
        try:
            # yfinance를 사용하여 환율 정보 가져오기
            ticker = yf.Ticker("USDKRW=X")
            # Ticker.info 대신 Ticker.history() 사용
            hist = ticker.history(period="1d")
            if not hist.empty:
                # 가장 최근의 종가 반환
                return hist['Close'].iloc[-1]
            else:
                # 데이터가 없을 경우 기본값 사용
                return 1300.0
        except Exception as e:
            print(f"yfinance 환율 조회 실패: {e}")
            # API 실패 시 기본값 사용
            return 1300.0
    
    @staticmethod
    def convert_to_krw(amount, currency_code):
        """통화를 원화로 변환"""
        if currency_code == 'KRW':
            return amount
        elif currency_code == 'USD':
            rate = CurrencyConverter.get_usd_to_krw_rate()
            return amount * Decimal(str(rate))
        else:
            # 다른 통화는 일단 그대로 반환 (필요시 추가)
            return amount


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
        
        # 총 투자 금액 계산 (통화 변환 적용)
        total_invested = Decimal('0')
        for holding in holdings:
            converted_amount = CurrencyConverter.convert_to_krw(
                holding.invested_amount, 
                holding.currency_code
            )
            total_invested += converted_amount
        
        # 총 시장 가치 계산 (최신 스냅샷에서)
        snapshot_filters = {'user_id': self.user_id}
        if self.asset_type:
            snapshot_filters['asset_type'] = self.asset_type
            
        latest_snapshots = PortfolioSnapshot.objects.filter(
            **snapshot_filters
        ).order_by('-snapshot_date')[:1]
        
        print(f"Debug: asset_type={self.asset_type}, snapshot_filters={snapshot_filters}")
        print(f"Debug: found {latest_snapshots.count()} snapshots")
        
        total_market_value = Decimal('0')
        if latest_snapshots.exists():
            # 스냅샷의 market_value도 통화 변환 적용
            for snapshot in latest_snapshots:
                converted_value = CurrencyConverter.convert_to_krw(
                    snapshot.market_value, 
                    snapshot.currency_code
                )
                total_market_value += converted_value
        
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
        
        # 일별로 그룹화하여 합계 계산 (통화 변환 적용)
        daily_data = {}
        for snapshot in snapshots:
            date_str = snapshot.snapshot_date.strftime('%Y-%m-%d')
            if date_str not in daily_data:
                daily_data[date_str] = {
                    'date': date_str,
                    'market_value': Decimal('0'),
                    'invested_amount': Decimal('0')
                }
            
            # 통화 변환 적용
            converted_market_value = CurrencyConverter.convert_to_krw(
                snapshot.market_value or Decimal('0'), 
                snapshot.currency_code
            )
            converted_invested_amount = CurrencyConverter.convert_to_krw(
                snapshot.invested_amount or Decimal('0'), 
                snapshot.currency_code
            )
            
            daily_data[date_str]['market_value'] += converted_market_value
            daily_data[date_str]['invested_amount'] += converted_invested_amount
        
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
        total_value = Decimal('0')
        for holding in holdings:
            converted_amount = CurrencyConverter.convert_to_krw(holding.invested_amount, holding.currency_code)
            total_value += converted_amount
        return float(total_value)
    
    def get_total_change(self):
        """총 자산 변화량 반환"""
        snapshots = PortfolioSnapshot.objects.filter(user_id=self.user_id).order_by('-snapshot_date')[:2]
        if len(snapshots) >= 2:
            # market_value 차이로 변화량 계산 (통화 변환 적용)
            current_value = float(CurrencyConverter.convert_to_krw(snapshots[0].market_value or 0, snapshots[0].currency_code))
            previous_value = float(CurrencyConverter.convert_to_krw(snapshots[1].market_value or 0, snapshots[1].currency_code))
            return current_value - previous_value
        return 0.0
    
    def get_total_change_percent(self):
        """총 자산 변화율 반환"""
        snapshots = PortfolioSnapshot.objects.filter(user_id=self.user_id).order_by('-snapshot_date')[:2]
        if len(snapshots) >= 2:
            # market_value 차이로 변화율 계산 (통화 변환 적용)
            current_value = float(CurrencyConverter.convert_to_krw(snapshots[0].market_value or 0, snapshots[0].currency_code))
            previous_value = float(CurrencyConverter.convert_to_krw(snapshots[1].market_value or 0, snapshots[1].currency_code))
            if previous_value > 0:
                return ((current_value - previous_value) / previous_value) * 100
        return 0.0
    
    def get_stock_holdings(self):
        """주식 보유 자산 반환"""
        holdings = PortfolioHolding.objects.filter(user_id=self.user_id, asset_type='stock')
        
        # Fetch all needed StockInfo objects in one query
        ticker_symbols = [h.stock_ticker_symbol for h in holdings if h.stock_ticker_symbol]
        stock_infos = StockInfo.objects.in_bulk(ticker_symbols) # Use in_bulk for a dict lookup

        results = []
        for h in holdings:
            print(f"보유 종목: {h.asset_name}, 통화: {h.currency_code}")
            stock_info = stock_infos.get(h.stock_ticker_symbol)
            # Use last_close_price as current price, fallback to avg_buy_price
            current_price = stock_info.last_close_price if stock_info and stock_info.last_close_price else h.avg_buy_price or 0

            total_quantity = h.total_quantity or 0
            avg_buy_price = h.avg_buy_price or 0

            invested_amount = total_quantity * avg_buy_price
            market_value = total_quantity * current_price
            pnl = market_value - invested_amount
            pnl_percentage = (pnl / invested_amount) * 100 if invested_amount > 0 else 0

            results.append({
                'name': h.asset_name,
                'ticker': h.stock_ticker_symbol or '',
                'sector': h.sector_or_region,
                'quantity': float(total_quantity),
                'avg_buy_price': float(avg_buy_price),
                'avg_buy_price_krw': float(CurrencyConverter.convert_to_krw(avg_buy_price, h.currency_code)),
                'invested_amount': float(invested_amount),
                'invested_amount_krw': float(CurrencyConverter.convert_to_krw(invested_amount, h.currency_code)),
                'market_value': float(market_value),
                'market_value_krw': float(CurrencyConverter.convert_to_krw(market_value, h.currency_code)),
                'pnl': float(pnl),
                'pnl_krw': float(CurrencyConverter.convert_to_krw(pnl, h.currency_code)),
                'pnl_percentage': float(pnl_percentage),
                'currency': h.currency_code or 'KRW',
                'country': 'US' if h.currency_code == 'USD' else 'KR'
            })
        return results
    
    def get_real_estate_holdings(self):
        """부동산 보유 자산 반환"""
        holdings = PortfolioHolding.objects.filter(user_id=self.user_id, asset_type='real_estate')
        return [
            {
                'name': h.asset_name,
                'region': h.sector_or_region,
                'quantity': float(h.total_quantity),
                'market_value': float(CurrencyConverter.convert_to_krw(h.invested_amount, h.currency_code)),
                'currency': 'KRW'  # 모든 값을 원화로 변환
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
            # 통화 변환 적용
            converted_amount = CurrencyConverter.convert_to_krw(holding.invested_amount, holding.currency_code)
            sector_data[sector] += float(converted_amount)
        
        return sector_data
    
    def get_region_breakdown(self):
        """지역별 분해 반환"""
        holdings = PortfolioHolding.objects.filter(user_id=self.user_id, asset_type='real_estate')
        region_data = {}
        
        for holding in holdings:
            region = holding.sector_or_region
            if region not in region_data:
                region_data[region] = 0
            # 통화 변환 적용
            converted_amount = CurrencyConverter.convert_to_krw(holding.invested_amount, holding.currency_code)
            region_data[region] += float(converted_amount)
        
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

<<<<<<< HEAD
# 메서드들 추가
add_portfolio_methods()
=======
        return {
            'total_entries': total_entries,
            'stock_entries': stock_entries,
            'real_estate_entries': real_estate_entries,
            'recent_entries': recent_entries
        }

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

def process_trade_for_portfolio(trade_id):
    """
    Updates PortfolioHolding and creates a PortfolioSnapshot from a single StockTrade.
    This should be the single source of truth for portfolio updates.
    """
    try:
        trade = StockTrade.objects.select_related('journal__user', 'journal__ticker_symbol').get(id=trade_id)
        journal = trade.journal
        user = journal.user
        stock_info = journal.ticker_symbol

        # It's crucial to recalculate journal aggregates before doing anything else.
        journal.recalculate_aggregates()
        # Reload the journal to get the fresh data from the update() call inside recalculate_aggregates
        journal.refresh_from_db()

        # Now, update the PortfolioHolding with the fresh data from the journal
        holding, created = PortfolioHolding.objects.update_or_create(
            user_id=user.id,
            asset_key=f"stock:{stock_info.ticker_symbol}",
            defaults={
                'asset_type': 'stock',
                'stock_ticker_symbol': stock_info.ticker_symbol,
                'asset_name': stock_info.stock_name,
                'sector_or_region': stock_info.sector or '기타',
                'currency_code': stock_info.currency or 'KRW',
                'total_quantity': journal.net_qty,
                'avg_buy_price': journal.avg_buy_price,
                'invested_amount': (journal.net_qty * journal.avg_buy_price) if journal.net_qty > 0 and journal.avg_buy_price is not None else 0,
                'realized_profit': journal.realized_pnl or 0,
                'total_buy_amount': journal.total_buy_qty * (journal.avg_buy_price or 0),
                'total_sell_amount': journal.total_sell_qty * (journal.avg_sell_price or 0),
            }
        )

        # Then, create a snapshot for the specific date of the trade.
        # This captures the state of the holding *after* this trade.
        # A more advanced implementation might need to update all subsequent snapshots,
        # but for now, this creates the necessary historical record.
        snapshot, snap_created = PortfolioSnapshot.objects.update_or_create(
            user_id=user.id,
            snapshot_date=trade.trade_date,
            asset_key=holding.asset_key,
            defaults={
                'asset_type': 'stock',
                'stock_ticker_symbol': holding.stock_ticker_symbol,
                'quantity': journal.net_qty,
                'avg_buy_price': journal.avg_buy_price,
                'invested_amount': holding.invested_amount,
                'market_price': trade.price_per_share, # Use the actual trade price for the snapshot
                'market_value': journal.net_qty * trade.price_per_share,
                'currency_code': holding.currency_code,
            }
        )
        print(f"Processed trade {trade.id}, {'created' if snap_created else 'updated'} snapshot for {trade.trade_date}.")

    except StockTrade.DoesNotExist:
        print(f"StockTrade with id={trade_id} not found.")
    except Exception as e:
        print(f"Error processing trade {trade_id} for portfolio: {e}")
>>>>>>> d8922d3 (전체적인 파일 수정)
