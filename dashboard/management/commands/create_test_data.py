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
        
        # 주식 자산들 (섹터별로 분류)
        stock_holdings = [
            {
                'ticker': '005930.KS',  # 삼성전자
                'name': '삼성전자',
                'sector': 'Technology',
                'quantity': Decimal('10'),
                'avg_price': Decimal('70000'),
            },
            {
                'ticker': '000660.KS',  # SK하이닉스
                'name': 'SK하이닉스',
                'sector': 'Technology',
                'quantity': Decimal('5'),
                'avg_price': Decimal('120000'),
            },
            {
                'ticker': '035420.KS',  # 네이버
                'name': '네이버',
                'sector': 'Technology',
                'quantity': Decimal('3'),
                'avg_price': Decimal('180000'),
            },
            {
                'ticker': 'AAPL',  # 애플
                'name': 'Apple Inc.',
                'sector': 'Technology',
                'quantity': Decimal('2'),
                'avg_price': Decimal('150000'),
            },
            # Healthcare 섹터
            {
                'ticker': '068270.KS',  # 셀트리온
                'name': '셀트리온',
                'sector': 'Healthcare',
                'quantity': Decimal('8'),
                'avg_price': Decimal('150000'),
            },
            {
                'ticker': '207940.KS',  # 삼성바이오로직스
                'name': '삼성바이오로직스',
                'sector': 'Healthcare',
                'quantity': Decimal('4'),
                'avg_price': Decimal('800000'),
            },
            # Finance 섹터
            {
                'ticker': '055550.KS',  # 신한지주
                'name': '신한지주',
                'sector': 'Finance',
                'quantity': Decimal('20'),
                'avg_price': Decimal('45000'),
            },
            {
                'ticker': '105560.KS',  # KB금융
                'name': 'KB금융',
                'sector': 'Finance',
                'quantity': Decimal('15'),
                'avg_price': Decimal('60000'),
            },
            # Consumer 섹터
            {
                'ticker': '017670.KS',  # SK텔레콤
                'name': 'SK텔레콤',
                'sector': 'Consumer',
                'quantity': Decimal('12'),
                'avg_price': Decimal('25000'),
            },
            {
                'ticker': '030200.KS',  # KT
                'name': 'KT',
                'sector': 'Consumer',
                'quantity': Decimal('10'),
                'avg_price': Decimal('30000'),
            },
            # Energy 섹터
            {
                'ticker': '096770.KS',  # SK이노베이션
                'name': 'SK이노베이션',
                'sector': 'Energy',
                'quantity': Decimal('6'),
                'avg_price': Decimal('100000'),
            },
            {
                'ticker': '010950.KS',  # S-Oil
                'name': 'S-Oil',
                'sector': 'Energy',
                'quantity': Decimal('8'),
                'avg_price': Decimal('80000'),
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
                'region': '강남구',
                'quantity': Decimal('1'),
                'avg_price': Decimal('1000000000'),  # 10억
            },
            {
                'property_id': 2,
                'name': '서초구 오피스텔',
                'region': '서초구',
                'quantity': Decimal('1'),
                'avg_price': Decimal('800000000'),  # 8억
            },
            {
                'property_id': 3,
                'name': '송파구 상가',
                'region': '송파구',
                'quantity': Decimal('1'),
                'avg_price': Decimal('600000000'),  # 6억
            },
            {
                'property_id': 4,
                'name': '마포구 빌라',
                'region': '마포구',
                'quantity': Decimal('1'),
                'avg_price': Decimal('400000000'),  # 4억
            },
            {
                'property_id': 5,
                'name': '용산구 원룸',
                'region': '용산구',
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
                
                invested_amount = holding.total_quantity * current_price
                
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
                        'invested_amount': invested_amount,
                        'currency_code': holding.currency_code,
                    }
                )
                
                if not created:
                    # 기존 스냅샷 업데이트
                    snapshot.market_price = current_price
                    snapshot.invested_amount = invested_amount
                    snapshot.save()
        
        self.stdout.write(f'Created snapshots for {holdings.count()} holdings over 30 days')
