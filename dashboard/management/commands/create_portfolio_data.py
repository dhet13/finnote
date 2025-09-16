from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
import random

from dashboard.models import PortfolioHolding, PortfolioSnapshot
from accounts.models import User


class Command(BaseCommand):
    help = 'Create portfolio data for dashboard testing'

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
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with ID {user_id} does not exist')
            )
            return
        
        if clear_existing:
            self.stdout.write('Clearing existing portfolio data...')
            PortfolioHolding.objects.filter(user=user).delete()
            PortfolioSnapshot.objects.filter(user=user).delete()
        
        # 1. 테스트용 보유 자산 생성
        self.create_test_holdings(user)
        
        # 2. 테스트용 스냅샷 데이터 생성
        self.create_test_snapshots(user)
        
        self.stdout.write(
            self.style.SUCCESS(f'Portfolio data created for user {user.my_ID}')
        )

    def create_test_holdings(self, user):
        """테스트용 보유 자산 생성"""
        self.stdout.write('Creating test holdings...')
        
        # 주식 자산들 (섹터별로 분류)
        stock_holdings = [
            # Technology 섹터
            {
                'ticker': '005930.KS',  # 삼성전자
                'name': '삼성전자',
                'sector': 'Technology',
                'quantity': Decimal('10'),
                'avg_price': Decimal('70000'),
                'market_value': Decimal('700000'),
            },
            {
                'ticker': '000660.KS',  # SK하이닉스
                'name': 'SK하이닉스',
                'sector': 'Technology',
                'quantity': Decimal('5'),
                'avg_price': Decimal('120000'),
                'market_value': Decimal('600000'),
            },
            {
                'ticker': '035420.KS',  # 네이버
                'name': '네이버',
                'sector': 'Technology',
                'quantity': Decimal('3'),
                'avg_price': Decimal('200000'),
                'market_value': Decimal('600000'),
            },
            {
                'ticker': '035720.KS',  # 카카오
                'name': '카카오',
                'sector': 'Technology',
                'quantity': Decimal('2'),
                'avg_price': Decimal('50000'),
                'market_value': Decimal('100000'),
            },
            # Healthcare 섹터
            {
                'ticker': '068270.KS',  # 셀트리온
                'name': '셀트리온',
                'sector': 'Healthcare',
                'quantity': Decimal('8'),
                'avg_price': Decimal('150000'),
                'market_value': Decimal('1200000'),
            },
            {
                'ticker': '207940.KS',  # 삼성바이오로직스
                'name': '삼성바이오로직스',
                'sector': 'Healthcare',
                'quantity': Decimal('4'),
                'avg_price': Decimal('800000'),
                'market_value': Decimal('3200000'),
            },
            # Finance 섹터
            {
                'ticker': '055550.KS',  # 신한지주
                'name': '신한지주',
                'sector': 'Finance',
                'quantity': Decimal('20'),
                'avg_price': Decimal('45000'),
                'market_value': Decimal('900000'),
            },
            {
                'ticker': '105560.KS',  # KB금융
                'name': 'KB금융',
                'sector': 'Finance',
                'quantity': Decimal('15'),
                'avg_price': Decimal('60000'),
                'market_value': Decimal('900000'),
            },
            # Consumer 섹터
            {
                'ticker': '017670.KS',  # SK텔레콤
                'name': 'SK텔레콤',
                'sector': 'Consumer',
                'quantity': Decimal('12'),
                'avg_price': Decimal('25000'),
                'market_value': Decimal('300000'),
            },
            {
                'ticker': '030200.KS',  # KT
                'name': 'KT',
                'sector': 'Consumer',
                'quantity': Decimal('10'),
                'avg_price': Decimal('30000'),
                'market_value': Decimal('300000'),
            },
            # Energy 섹터
            {
                'ticker': '096770.KS',  # SK이노베이션
                'name': 'SK이노베이션',
                'sector': 'Energy',
                'quantity': Decimal('6'),
                'avg_price': Decimal('100000'),
                'market_value': Decimal('600000'),
            },
            {
                'ticker': '010950.KS',  # S-Oil
                'name': 'S-Oil',
                'sector': 'Energy',
                'quantity': Decimal('8'),
                'avg_price': Decimal('80000'),
                'market_value': Decimal('640000'),
            },
        ]
        
        # 부동산 자산들
        property_holdings = [
            {
                'name': '강남구 아파트',
                'region': '강남구',
                'quantity': Decimal('1'),
                'avg_price': Decimal('1000000000'),
                'market_value': Decimal('1200000000'),
            },
            {
                'name': '서초구 오피스텔',
                'region': '서초구',
                'quantity': Decimal('1'),
                'avg_price': Decimal('800000000'),
                'market_value': Decimal('900000000'),
            },
            {
                'name': '송파구 상가',
                'region': '송파구',
                'quantity': Decimal('1'),
                'avg_price': Decimal('600000000'),
                'market_value': Decimal('700000000'),
            },
            {
                'name': '마포구 빌라',
                'region': '마포구',
                'quantity': Decimal('1'),
                'avg_price': Decimal('400000000'),
                'market_value': Decimal('450000000'),
            },
            {
                'name': '용산구 원룸',
                'region': '용산구',
                'quantity': Decimal('1'),
                'avg_price': Decimal('200000000'),
                'market_value': Decimal('250000000'),
            },
        ]
        
        # 주식 자산 생성
        for holding in stock_holdings:
            PortfolioHolding.objects.create(
                user=user,
                asset_type='stock',
                asset_name=holding['name'],
                ticker=holding['ticker'],
                sector_or_region=holding['sector'],
                currency_code='KRW',
                quantity=holding['quantity'],
                avg_buy_price=holding['avg_price'],
                invested_amount=holding['market_value'],
                total_buy_amount=holding['market_value'],
                market_value=holding['market_value']
            )
            self.stdout.write(f'  - {holding["name"]} ({holding["sector"]})')
        
        # 부동산 자산 생성
        for holding in property_holdings:
            PortfolioHolding.objects.create(
                user=user,
                asset_type='real_estate',
                asset_name=holding['name'],
                ticker='',
                sector_or_region=holding['region'],
                currency_code='KRW',
                quantity=holding['quantity'],
                avg_buy_price=holding['avg_price'],
                invested_amount=holding['market_value'],
                total_buy_amount=holding['market_value'],
                market_value=holding['market_value']
            )
            self.stdout.write(f'  - {holding["name"]} ({holding["region"]})')

    def create_test_snapshots(self, user):
        """테스트용 스냅샷 데이터 생성"""
        self.stdout.write('Creating test snapshots...')
        
        # 최근 30일간의 스냅샷 데이터 생성
        base_value = Decimal('10000000')  # 1천만원 기준
        
        for i in range(30):
            snapshot_date = date.today() - timedelta(days=i)
            
            # 랜덤한 변동률 (-5% ~ +5%)
            change_percent = Decimal(str(random.uniform(-5, 5)))
            change_amount = base_value * change_percent / 100
            total_value = base_value + change_amount
            
            PortfolioSnapshot.objects.create(
                user=user,
                snapshot_date=snapshot_date,
                total_value=total_value,
                total_change=change_amount,
                total_change_percent=change_percent
            )
        
        self.stdout.write(f'  - Created 30 snapshots for user {user.my_ID}')
