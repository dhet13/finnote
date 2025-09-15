from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
import random

from dashboard.models import PortfolioHolding, PortfolioSnapshot


class Command(BaseCommand):
    help = 'Create test data for dashboard testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            default=1,
            help='User ID to create test data for (default: 1)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test data before creating new data',
        )

    def handle(self, *args, **options):
        user_id = options['user_id']
        clear_existing = options['clear']
        
        if clear_existing:
            self.stdout.write('Clearing existing test data...')
            PortfolioHolding.objects.filter(user_id=user_id).delete()
            PortfolioSnapshot.objects.filter(user_id=user_id).delete()
        
        # 1. 테스트용 보유 자산 생성
        self.create_test_holdings(user_id)
        
        # 2. 테스트용 스냅샷 데이터 생성
        self.create_test_snapshots(user_id)
        
        self.stdout.write(
            self.style.SUCCESS(f'Test data created for user {user_id}')
        )

    def create_test_holdings(self, user_id):
        """테스트용 보유 자산 생성"""
        self.stdout.write('Creating test holdings...')
        
        # 주식 자산들
        stock_holdings = [
            {
                'ticker': '005930.KS',  # 삼성전자
                'name': '삼성전자',
                'sector': 'IT/전자',
                'quantity': Decimal('10'),
                'avg_price': Decimal('70000'),
            },
            {
                'ticker': '000660.KS',  # SK하이닉스
                'name': 'SK하이닉스',
                'sector': 'IT/전자',
                'quantity': Decimal('5'),
                'avg_price': Decimal('120000'),
            },
            {
                'ticker': '035420.KS',  # 네이버
                'name': '네이버',
                'sector': 'IT/서비스',
                'quantity': Decimal('3'),
                'avg_price': Decimal('180000'),
            },
            {
                'ticker': 'AAPL',  # 애플
                'name': 'Apple Inc.',
                'sector': 'IT/전자',
                'quantity': Decimal('2'),
                'avg_price': Decimal('150000'),
            },
        ]
        
        for stock in stock_holdings:
            holding, created = PortfolioHolding.objects.get_or_create(
                user_id=user_id,
                asset_key=f"stock:{stock['ticker']}",
                defaults={
                    'asset_type': 'stock',
                    'stock_ticker_symbol': stock['ticker'],
                    'asset_name': stock['name'],
                    'sector_or_region': stock['sector'],
                    'currency_code': 'KRW',
                    'total_quantity': stock['quantity'],
                    'avg_buy_price': stock['avg_price'],
                    'invested_amount': stock['quantity'] * stock['avg_price'],
                    'realized_profit': Decimal('0'),
                    'total_buy_amount': stock['quantity'] * stock['avg_price'],
                    'total_sell_amount': Decimal('0'),
                }
            )
            
            if created:
                self.stdout.write(f'Created stock holding: {stock["name"]}')
        
        # 부동산 자산들
        real_estate_holdings = [
            {
                'property_id': 1,
                'name': '강남구 아파트',
                'region': '서울 강남구',
                'quantity': Decimal('1'),
                'avg_price': Decimal('500000000'),  # 5억
            },
            {
                'property_id': 2,
                'name': '부산 해운대 오피스텔',
                'region': '부산 해운대구',
                'quantity': Decimal('1'),
                'avg_price': Decimal('200000000'),  # 2억
            },
        ]
        
        for re in real_estate_holdings:
            holding, created = PortfolioHolding.objects.get_or_create(
                user_id=user_id,
                asset_key=f"re:{re['property_id']}",
                defaults={
                    'asset_type': 'real_estate',
                    'property_info_id': re['property_id'],
                    'asset_name': re['name'],
                    'sector_or_region': re['region'],
                    'currency_code': 'KRW',
                    'total_quantity': re['quantity'],
                    'avg_buy_price': re['avg_price'],
                    'invested_amount': re['quantity'] * re['avg_price'],
                    'realized_profit': Decimal('0'),
                    'total_buy_amount': re['quantity'] * re['avg_price'],
                    'total_sell_amount': Decimal('0'),
                }
            )
            
            if created:
                self.stdout.write(f'Created real estate holding: {re["name"]}')

    def create_test_snapshots(self, user_id):
        """테스트용 스냅샷 데이터 생성 (최근 30일)"""
        self.stdout.write('Creating test snapshots...')
        
        # 최근 30일간의 스냅샷 데이터 생성
        today = date.today()
        holdings = PortfolioHolding.objects.filter(user_id=user_id)
        
        for days_ago in range(30, -1, -1):  # 30일 전부터 오늘까지
            snapshot_date = today - timedelta(days=days_ago)
            
            for holding in holdings:
                # 가격 변동 시뮬레이션 (일일 -5% ~ +5% 랜덤 변동)
                base_price = holding.avg_buy_price
                daily_change = random.uniform(-0.05, 0.05)  # -5% ~ +5%
                current_price = base_price * (1 + Decimal(str(daily_change)))
                
                # 시간이 지날수록 약간의 상승 트렌드 추가
                trend_factor = 1 + (30 - days_ago) * 0.001  # 30일간 3% 상승
                current_price = current_price * Decimal(str(trend_factor))
                
                market_value = holding.total_quantity * current_price
                
                snapshot, created = PortfolioSnapshot.objects.get_or_create(
                    user_id=user_id,
                    snapshot_date=snapshot_date,
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
        
        self.stdout.write(f'Created snapshots for {holdings.count()} holdings over 30 days')
