from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import yfinance as yf
import FinanceDataReader as fdr
from datetime import date

from dashboard.models import PortfolioHolding, PortfolioSnapshot


class Command(BaseCommand):
    help = 'Update market values for all portfolio holdings and create snapshots'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # 모든 보유 자산 조회
        holdings = PortfolioHolding.objects.all()
        
        if not holdings.exists():
            self.stdout.write(self.style.WARNING('No portfolio holdings found'))
            return
        
        updated_count = 0
        error_count = 0
        
        for holding in holdings:
            try:
                current_price = self.get_current_price(holding)
                if current_price is None:
                    self.stdout.write(
                        self.style.ERROR(f'Could not get price for {holding.asset_key}')
                    )
                    error_count += 1
                    continue
                
                # market_value 계산
                market_value = holding.total_quantity * current_price
                
                if not dry_run:
                    # PortfolioSnapshot에 저장
                    snapshot, created = PortfolioSnapshot.objects.get_or_create(
                        user_id=holding.user_id,
                        snapshot_date=timezone.now().date(),
                        asset_key=holding.asset_key,
                        defaults={
                            'asset_type': holding.asset_type,
                            'stock_ticker_symbol': holding.stock_ticker_symbol,
                            'property_info_id': holding.property_info_id,
                            'quantity': holding.total_quantity,
                            'avg_buy_price': holding.avg_buy_price,
                            'invested_amount': holding.invested_amount,
                            'market_price': current_price,
                            'market_value': market_value,
                            'currency_code': holding.currency_code,
                        }
                    )
                    
                    if not created:
                        # 기존 스냅샷 업데이트
                        snapshot.market_price = current_price
                        snapshot.market_value = market_value
                        snapshot.save()
                
                self.stdout.write(
                    f'{"[DRY RUN] " if dry_run else ""}Updated {holding.asset_key}: '
                    f'Price={current_price}, Value={market_value}'
                )
                updated_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error updating {holding.asset_key}: {str(e)}')
                )
                error_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'{"[DRY RUN] " if dry_run else ""}Completed: {updated_count} updated, {error_count} errors'
            )
        )

    def get_current_price(self, holding):
        """자산 유형에 따라 현재 가격을 조회합니다."""
        try:
            if holding.asset_type == 'stock':
                if holding.stock_ticker_symbol:
                    # 한국 주식 (KOSPI/KOSDAQ)
                    if holding.stock_ticker_symbol.endswith('.KS') or holding.stock_ticker_symbol.endswith('.KQ'):
                        ticker = holding.stock_ticker_symbol
                    else:
                        # .KS 추가 (KOSPI)
                        ticker = f"{holding.stock_ticker_symbol}.KS"
                    
                    try:
                        # FinanceDataReader로 한국 주식 가격 조회
                        df = fdr.DataReader(ticker, date.today())
                        if not df.empty:
                            return Decimal(str(df['Close'].iloc[-1]))
                    except:
                        pass
                    
                    # yfinance로 시도
                    ticker_obj = yf.Ticker(holding.stock_ticker_symbol)
                    hist = ticker_obj.history(period='1d')
                    if not hist.empty:
                        return Decimal(str(hist['Close'].iloc[-1]))
                
            elif holding.asset_type == 'real_estate':
                # 부동산 가격은 별도 API 필요 (현재는 임시값)
                # TODO: 실제 부동산 가격 API 연동
                return Decimal('1000000')  # 임시값
            
            return None
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error fetching price for {holding.asset_key}: {str(e)}')
            )
            return None
