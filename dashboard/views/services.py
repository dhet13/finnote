# apps/dashboard/views/services.py
from django.db.models import Sum, Q
from decimal import Decimal
from datetime import datetime, timedelta
from dashboard.models import PortfolioHolding, PortfolioSnapshot, AssetLogUnified
from journals.models import StockJournal, StockInfo, StockTrade
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
            # amount를 Decimal로 변환하고 rate도 Decimal로 변환
            amount_decimal = Decimal(str(amount)) if not isinstance(amount, Decimal) else amount
            rate_decimal = Decimal(str(rate))
            return amount_decimal * rate_decimal
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
            print(f"🚀 get_data_payload 시작: user_id={self.user_id}, asset_type={self.asset_type}")

            # 자산 현황 데이터
            holdings_data = self._get_holdings_data()
            print(f"💰 holdings_data 결과: {holdings_data}")

            # 시계열 데이터
            timeseries_data = self._get_timeseries_data()
            print(f"📈 timeseries_data 길이: {len(timeseries_data)}")

            result = {
                'holdings': holdings_data,
                'timeseries': timeseries_data,
                'status': 'success'
            }
            print(f"🎯 최종 API 응답: {result}")
            return result
        except Exception as e:
            error_result = {
                'error': str(e),
                'status': 'error'
            }
            print(f"❌ API 오류: {error_result}")
            return error_result
    
    def _get_holdings_data(self):
        """보유 자산 데이터 조회"""
        print(f"=== _get_holdings_data 디버깅 ===")
        print(f"user_id: {self.user_id}")
        print(f"asset_type: {self.asset_type}")

        # 먼저 사용자가 가진 실제 매매일지 데이터 확인
        from journals.models import StockJournal, REDeal
        stock_journals = StockJournal.objects.filter(user_id=self.user_id)
        re_deals = REDeal.objects.filter(user_id=self.user_id)
        print(f"실제 StockJournal 개수: {stock_journals.count()}")
        print(f"실제 REDeal 개수: {re_deals.count()}")

        # PortfolioHolding 테이블이 비어있으면 동기화가 안된 상태
        holdings_count = PortfolioHolding.objects.filter(user_id=self.user_id).count()
        print(f"PortfolioHolding 개수: {holdings_count}")

        if holdings_count == 0 and (stock_journals.exists() or re_deals.exists()):
            print("⚠️  매매일지는 있지만 PortfolioHolding이 비어있음 - 동기화 필요")
            # 임시로 실시간 계산해서 반환
            return self._calculate_from_journals_directly()

        # 필터 조건 설정
        filters = {'user_id': self.user_id}
        if self.asset_type:
            filters['asset_type'] = self.asset_type

        print(f"필터 조건: {filters}")

        # 보유 자산 조회
        holdings = PortfolioHolding.objects.filter(**filters)
        print(f"필터링된 PortfolioHolding 개수: {holdings.count()}")

        for holding in holdings:
            print(f"  - {holding.asset_name}: {holding.invested_amount}")

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

        # 스냅샷 상세 정보 출력
        for snapshot in latest_snapshots:
            print(f"📸 스냅샷 상세: date={snapshot.snapshot_date}, market_value={snapshot.market_value}, currency={snapshot.currency_code}")

        total_market_value = Decimal('0')

        # 스냅샷의 market_value가 0인 경우가 많아서, holdings에서 직접 계산
        print("💰 스냅샷 대신 PortfolioHolding에서 직접 시장가치 계산")
        for holding in holdings:
            if holding.asset_type == 'stock':
                # 주식: 보유수량 × 평균매수가 (임시로 매수가를 시장가로 사용)
                if holding.total_quantity and holding.avg_buy_price:
                    # Decimal 타입으로 안전하게 곱셈
                    market_value = Decimal(str(holding.total_quantity)) * Decimal(str(holding.avg_buy_price))
                    converted_value = CurrencyConverter.convert_to_krw(market_value, holding.currency_code)
                    total_market_value += converted_value
                    print(f"📈 {holding.asset_name}: {holding.total_quantity} × {holding.avg_buy_price} = {converted_value} KRW")
            else:
                # 부동산: 투자금액을 시장가치로 사용
                converted_value = CurrencyConverter.convert_to_krw(holding.invested_amount, holding.currency_code)
                total_market_value += converted_value
                print(f"🏠 {holding.asset_name}: {converted_value} KRW")

        print(f"📊 최종 계산된 total_market_value: {total_market_value}")

        # 수익률 계산
        if total_invested > 0:
            return_rate = ((total_market_value - total_invested) / total_invested) * Decimal('100')
        else:
            return_rate = Decimal('0')

        result = {
            'total_invested': float(total_invested),
            'total_market_value': float(total_market_value),
            'return_rate': float(return_rate),
            'return_amount': float(total_market_value - total_invested),
            'holdings_count': holdings.count()
        }
        print(f"🏦 기존 로직 최종 반환 데이터: {result}")
        return result

    def _calculate_from_journals_directly(self):
        """매매일지에서 직접 계산 (임시 대안)"""
        from journals.models import StockJournal, REDeal

        total_invested = Decimal('0')
        total_market_value = Decimal('0')
        holdings_count = 0

        # 주식 자산 계산
        if not self.asset_type or self.asset_type == 'stock':
            stock_journals = StockJournal.objects.filter(user_id=self.user_id)
            for journal in stock_journals:
                if journal.net_qty and journal.net_qty > 0 and journal.avg_buy_price:
                    # Decimal 타입으로 안전하게 곱셈
                    invested = Decimal(str(journal.net_qty)) * Decimal(str(journal.avg_buy_price))
                    market_value = invested  # 임시로 투자금액을 시장가치로 사용

                    # 통화 변환
                    currency = journal.ticker_symbol.currency or 'KRW'
                    converted_invested = CurrencyConverter.convert_to_krw(invested, currency)
                    converted_market = CurrencyConverter.convert_to_krw(market_value, currency)

                    total_invested += converted_invested
                    total_market_value += converted_market
                    holdings_count += 1

        # 부동산 자산 계산
        if not self.asset_type or self.asset_type == 'real_estate':
            re_deals = REDeal.objects.filter(user_id=self.user_id)
            for deal in re_deals:
                invested = deal.amount_main
                market_value = invested  # 임시로 투자금액을 시장가치로 사용

                # 부동산은 KRW
                total_invested += invested
                total_market_value += market_value
                holdings_count += 1

        # 수익률 계산
        if total_invested > 0:
            return_rate = ((total_market_value - total_invested) / total_invested) * Decimal('100')
        else:
            return_rate = Decimal('0')

        print(f"📊 직접 계산 결과: 투자금액={total_invested}, 시장가치={total_market_value}, 보유자산={holdings_count}")

        result = {
            'total_invested': float(total_invested),
            'total_market_value': float(total_market_value),
            'return_rate': float(return_rate),
            'return_amount': float(total_market_value - total_invested),
            'holdings_count': holdings_count,
            'calculated_directly': True
        }
        print(f"🔍 최종 반환 데이터: {result}")
        return result
    
    def _get_timeseries_data(self):
        """시계열 데이터 조회 - 매매일지 작성 날짜 기반"""
        print("📈 timeseries 데이터 실시간 계산 시작")

        from journals.models import StockJournal, StockTrade, REDeal
        from datetime import datetime, timedelta

        # 실제 매매일지 작성 날짜 범위 구하기
        earliest_stock_date = None
        earliest_re_date = None

        # 주식 매매일지 최초 작성일
        if not self.asset_type or self.asset_type == 'stock':
            earliest_stock_journal = StockJournal.objects.filter(user_id=self.user_id).order_by('created_at').first()
            if earliest_stock_journal:
                earliest_stock_date = earliest_stock_journal.created_at.date()
                print(f"📅 최초 주식 매매일지 작성일: {earliest_stock_date}")

        # 부동산 거래 최초 작성일
        if not self.asset_type or self.asset_type == 'real_estate':
            earliest_re_deal = REDeal.objects.filter(user_id=self.user_id).order_by('created_at').first()
            if earliest_re_deal:
                earliest_re_date = earliest_re_deal.created_at.date()
                print(f"🏠 최초 부동산 거래 작성일: {earliest_re_date}")

        # 전체 최초 작성일 결정
        earliest_dates = [d for d in [earliest_stock_date, earliest_re_date] if d is not None]
        if not earliest_dates:
            print("📭 매매일지가 없어서 빈 시계열 반환")
            return []

        start_date = min(earliest_dates)
        today = datetime.now().date()
        print(f"📊 시계열 범위: {start_date} ~ {today}")

        # 현재 holdings 데이터 기반 계산
        filters = {'user_id': self.user_id}
        if self.asset_type:
            filters['asset_type'] = self.asset_type

        holdings = PortfolioHolding.objects.filter(**filters)

        # 총 투자금액과 현재 시장가치 계산
        total_invested = Decimal('0')
        total_market_value = Decimal('0')

        for holding in holdings:
            # 투자금액
            converted_invested = CurrencyConverter.convert_to_krw(
                holding.invested_amount, holding.currency_code
            )
            total_invested += converted_invested

            # 시장가치 (매수가 기준)
            if holding.asset_type == 'stock' and holding.total_quantity and holding.avg_buy_price:
                # Decimal 타입으로 안전하게 곱셈
                market_value = Decimal(str(holding.total_quantity)) * Decimal(str(holding.avg_buy_price))
                converted_market = CurrencyConverter.convert_to_krw(market_value, holding.currency_code)
                total_market_value += converted_market
            else:
                total_market_value += converted_invested

        # 30일치 시계열 데이터 생성
        timeseries = []
        days_range = min(30, (today - start_date).days + 1)  # 최대 30일, 실제 기간이 더 짧으면 실제 기간

        for i in range(days_range):
            current_date = today - timedelta(days=days_range - 1 - i)

            # 시간에 따른 가상의 변화 (실제로는 각 날짜별 실제 데이터가 필요)
            progress_ratio = (i + 1) / days_range  # 0 ~ 1

            # 초기에는 낮은 가치에서 시작해서 점진적으로 현재 가치로 증가
            simulated_market_value = total_invested + (total_market_value - total_invested) * Decimal(str(progress_ratio))

            # 수익률 계산
            if total_invested > 0:
                cumulative_return_rate = ((simulated_market_value - total_invested) / total_invested) * Decimal('100')
            else:
                cumulative_return_rate = Decimal('0')

            # 일일 변화율 (전일 대비)
            if i > 0:
                prev_value = total_invested + (total_market_value - total_invested) * Decimal(str((i) / days_range))
                daily_return_rate = ((simulated_market_value - prev_value) / prev_value) * Decimal('100') if prev_value > 0 else 0
            else:
                daily_return_rate = 0

            timeseries.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'market_value': float(simulated_market_value),
                'invested_amount': float(total_invested),
                'return_rate': float(daily_return_rate),
                'cumulative_return_rate': float(cumulative_return_rate)
            })

        print(f"📊 생성된 timeseries 개수: {len(timeseries)}, 기간: {start_date} ~ {today}")
        return timeseries
    
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
            print(f"보유 종목: {h.asset_name}, 통화: {h.currency_code}, 티커: {h.stock_ticker_symbol}")
            stock_info = stock_infos.get(h.stock_ticker_symbol)
            # Use last_close_price as current price, fallback to avg_buy_price
            current_price = stock_info.last_close_price if stock_info and stock_info.last_close_price else h.avg_buy_price or 0
            
            # StockInfo에서 통화 정보 가져오기 (더 정확한 판단을 위해)
            actual_currency = None
            if stock_info and hasattr(stock_info, 'currency') and stock_info.currency:
                actual_currency = stock_info.currency
            elif h.currency_code:
                actual_currency = h.currency_code
            else:
                actual_currency = 'KRW'  # 기본값

            total_quantity = h.total_quantity or 0
            avg_buy_price = h.avg_buy_price or 0

            # Decimal 타입으로 안전하게 곱셈
            invested_amount = Decimal(str(total_quantity)) * Decimal(str(avg_buy_price))
            market_value = Decimal(str(total_quantity)) * Decimal(str(current_price))
            pnl = market_value - invested_amount
            pnl_percentage = (pnl / invested_amount) * Decimal('100') if invested_amount > 0 else 0

            results.append({
                'name': h.asset_name,
                'ticker': h.stock_ticker_symbol or '',
                'sector': h.sector_or_region,
                'quantity': float(total_quantity),
                'avg_buy_price': float(avg_buy_price),
                'avg_buy_price_krw': float(CurrencyConverter.convert_to_krw(avg_buy_price, actual_currency)),
                'invested_amount': float(invested_amount),
                'invested_amount_krw': float(CurrencyConverter.convert_to_krw(invested_amount, actual_currency)),
                'market_value': float(market_value),
                'market_value_krw': float(CurrencyConverter.convert_to_krw(market_value, actual_currency)),
                'pnl': float(pnl),
                'pnl_krw': float(CurrencyConverter.convert_to_krw(pnl, actual_currency)),
                'pnl_percentage': float(pnl_percentage),
                'currency': actual_currency,
                'country': 'US' if actual_currency == 'USD' else 'KR'
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
    
    def get_recent_journal_entries(self, limit=10):
        """최근 매매일지 항목 반환"""
        from home.models import Post
        from accounts.models import User
        
        # Post 모델에서 직접 매매일지 데이터 가져오기
        posts = Post.objects.filter(user_id=self.user_id).order_by('-created_at')[:limit]
        
        journal_entries = []
        for post in posts:
            # embed_payload_json에서 거래 정보 추출
            embed_data = post.embed_payload_json or {}
            
            journal_entries.append({
                'id': post.id,
                'content': post.content,
                'asset_name': embed_data.get('asset_name', 'Unknown'),
                'asset_type': embed_data.get('asset_type', 'other'),
                'total_amount': float(embed_data.get('total_amount', 0)) if embed_data.get('total_amount') else 0,
                'trade_date': embed_data.get('trade_date', post.created_at),
                'created_at': post.created_at,
                'embed_payload': embed_data
            })
        
        return journal_entries
    
    def get_journal_statistics(self):
        """매매일지 통계 반환"""
        from home.models import Post
        from accounts.models import User
        from datetime import datetime, timedelta
        
        # Post 모델에서 직접 매매일지 데이터 가져오기
        posts = Post.objects.filter(user_id=self.user_id)
        
        total_entries = posts.count()
        
        # asset_type별 분류
        stock_entries = 0
        real_estate_entries = 0
        
        for post in posts:
            embed_data = post.embed_payload_json or {}
            asset_type = embed_data.get('asset_type', 'other')
            if asset_type == 'stock':
                stock_entries += 1
            elif asset_type == 'real_estate':
                real_estate_entries += 1
        
        # 최근 30일간 작성한 매매일지 수
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_entries = posts.filter(created_at__gte=thirty_days_ago).count()

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
                'invested_amount': (Decimal(str(journal.net_qty)) * Decimal(str(journal.avg_buy_price))) if journal.net_qty > 0 and journal.avg_buy_price is not None else 0,
                'realized_profit': journal.realized_pnl or 0,
                'total_buy_amount': Decimal(str(journal.total_buy_qty)) * Decimal(str(journal.avg_buy_price or 0)),
                'total_sell_amount': Decimal(str(journal.total_sell_qty)) * Decimal(str(journal.avg_sell_price or 0)),
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
                'market_value': Decimal(str(journal.net_qty)) * Decimal(str(trade.price_per_share)),
                'currency_code': holding.currency_code,
            }
        )
        print(f"Processed trade {trade.id}, {'created' if snap_created else 'updated'} snapshot for {trade.trade_date}.")

    except StockTrade.DoesNotExist:
        print(f"StockTrade with id={trade_id} not found.")
    except Exception as e:
        print(f"Error processing trade {trade_id} for portfolio: {e}")