from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from journals.models import StockJournal, StockTrade, REDeal
from dashboard.models import PortfolioHolding, PortfolioSnapshot


class Command(BaseCommand):
    help = 'Sync existing StockJournal and REDeal data to PortfolioHolding'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # 1. 주식 자산 동기화
        self.sync_stock_holdings(dry_run)
        
        # 2. 부동산 자산 동기화
        self.sync_real_estate_holdings(dry_run)

    def sync_stock_holdings(self, dry_run):
        """StockJournal 데이터를 PortfolioHolding으로 동기화"""
        self.stdout.write('Syncing stock holdings...')
        
        stock_journals = StockJournal.objects.all()
        synced_count = 0
        
        for journal in stock_journals:
            try:
                # 해당 주식의 모든 거래 내역 조회
                trades = StockTrade.objects.filter(journal=journal)
                
                if not trades.exists():
                    self.stdout.write(f'No trades found for {journal.ticker_symbol.ticker_symbol}')
                    continue
                
                # 총 수량 계산 (매수 - 매도)
                total_buy_quantity = sum(
                    trade.quantity for trade in trades if trade.side == 'BUY'
                )
                total_sell_quantity = sum(
                    trade.quantity for trade in trades if trade.side == 'SELL'
                )
                current_quantity = total_buy_quantity - total_sell_quantity
                
                if current_quantity <= 0:
                    self.stdout.write(f'No holdings for {journal.ticker_symbol.ticker_symbol}')
                    continue
                
                # 평균 매수 가격 계산
                total_buy_amount = sum(
                    trade.price_per_share * trade.quantity for trade in trades if trade.side == 'BUY'
                )
                avg_buy_price = total_buy_amount / total_buy_quantity if total_buy_quantity > 0 else Decimal('0')
                
                # 총 투자 금액
                invested_amount = total_buy_amount - sum(
                    trade.price_per_share * trade.quantity for trade in trades if trade.side == 'SELL'
                )
                
                # 실현 손익 계산
                realized_profit = sum(
                    (trade.price_per_share - avg_buy_price) * trade.quantity 
                    for trade in trades if trade.side == 'SELL'
                )
                
                # 주식 정보에서 섹터와 통화 정보 가져오기
                stock_info = journal.ticker_symbol
                sector = stock_info.sector if stock_info.sector else 'Unknown'
                currency = stock_info.currency if stock_info.currency else 'KRW'
                
                if not dry_run:
                    # PortfolioHolding 생성 또는 업데이트
                    holding, created = PortfolioHolding.objects.get_or_create(
                        user_id=journal.user.id,
                        asset_key=f"stock:{journal.ticker_symbol.ticker_symbol}",
                        defaults={
                            'asset_type': 'stock',
                            'stock_ticker_symbol': journal.ticker_symbol.ticker_symbol,
                            'asset_name': journal.ticker_symbol.stock_name,
                            'sector_or_region': sector,  # StockInfo.sector 사용
                            'currency_code': currency,  # StockInfo.currency 사용
                            'total_quantity': current_quantity,
                            'avg_buy_price': avg_buy_price,
                            'invested_amount': invested_amount,
                            'realized_profit': realized_profit,
                            'total_buy_amount': total_buy_amount,
                            'total_sell_amount': sum(
                                trade.price_per_share * trade.quantity 
                                for trade in trades if trade.side == 'SELL'
                            ),
                        }
                    )
                    
                    if not created:
                        # 기존 데이터 업데이트
                        holding.total_quantity = current_quantity
                        holding.avg_buy_price = avg_buy_price
                        holding.invested_amount = invested_amount
                        holding.realized_profit = realized_profit
                        holding.sector_or_region = sector  # 섹터 정보 업데이트
                        holding.currency_code = currency  # 통화 정보 업데이트
                        holding.save()
                
                self.stdout.write(
                    f'{"[DRY RUN] " if dry_run else ""}Synced {journal.ticker_symbol.ticker_symbol}: '
                    f'Quantity={current_quantity}, AvgPrice={avg_buy_price}'
                )
                synced_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error syncing {journal.ticker_symbol.ticker_symbol}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'{"[DRY RUN] " if dry_run else ""}Synced {synced_count} stock holdings')
        )

    def sync_real_estate_holdings(self, dry_run):
        """REDeal 데이터를 PortfolioHolding으로 동기화"""
        self.stdout.write('Syncing real estate holdings...')
        
        re_deals = REDeal.objects.all()
        synced_count = 0
        
        for deal in re_deals:
            try:
                # 부동산 정보에서 지역 정보 가져오기
                property_info = deal.property_info
                region = f"{property_info.address_base} {property_info.dong}" if property_info.address_base else 'Unknown'
                
                # 부동산 거래는 보통 매수만 있으므로 단순화
                if not dry_run:
                    holding, created = PortfolioHolding.objects.get_or_create(
                        user_id=deal.user.id,
                        asset_key=f"re:{deal.property_info.id}",
                        defaults={
                            'asset_type': 'real_estate',
                            'property_info_id': deal.property_info.id,
                            'asset_name': property_info.building_name,
                            'sector_or_region': region,  # address_base + dong 조합
                            'currency_code': 'KRW',  # 부동산은 기본적으로 KRW
                            'total_quantity': Decimal('1'),  # 부동산은 1개 단위
                            'avg_buy_price': deal.amount_main,  # 매매가/전세가/보증금
                            'invested_amount': deal.amount_main,
                            'realized_profit': Decimal('0'),
                            'total_buy_amount': deal.amount_main,
                            'total_sell_amount': Decimal('0'),
                        }
                    )
                    
                    if not created:
                        holding.avg_buy_price = deal.amount_main
                        holding.invested_amount = deal.amount_main
                        holding.sector_or_region = region  # 지역 정보 업데이트
                        holding.save()
                
                self.stdout.write(
                    f'{"[DRY RUN] " if dry_run else ""}Synced real estate: '
                    f'{property_info.building_name} - {deal.amount_main}'
                )
                synced_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error syncing real estate {deal.id}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'{"[DRY RUN] " if dry_run else ""}Synced {synced_count} real estate holdings')
        )
