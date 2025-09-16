#!/usr/bin/env python
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from dashboard.models import PortfolioHolding, PortfolioSnapshot
from accounts.models import User
import random
from decimal import Decimal
from datetime import datetime, timedelta

def create_portfolio_data():
    try:
        # 사용자 확인
        user = User.objects.get(id=1)
        print(f'사용자: {user.my_ID}')

        # 기존 데이터 삭제
        PortfolioHolding.objects.filter(user=user).delete()
        PortfolioSnapshot.objects.filter(user=user).delete()
        print('기존 데이터 삭제 완료')

        # 주식 포트폴리오 데이터 생성
        stock_sectors = ['Technology', 'Healthcare', 'Finance', 'Consumer', 'Energy', 'Industrial']
        stock_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC']

        for i, (sector, ticker) in enumerate(zip(stock_sectors, stock_tickers)):
            PortfolioHolding.objects.create(
                user=user,
                asset_type='stock',
                asset_name=f'{ticker} 주식',
                ticker=ticker,
                sector_or_region=sector,
                currency_code='USD',
                quantity=random.randint(10, 100),
                avg_buy_price=Decimal(str(random.uniform(50, 500))),
                invested_amount=Decimal(str(random.uniform(1000, 10000))),
                total_buy_amount=Decimal(str(random.uniform(1000, 10000))),
                market_value=Decimal(str(random.uniform(1000, 10000)))
            )
            print(f'주식 데이터 생성: {ticker} - {sector}')

        # 부동산 포트폴리오 데이터 생성
        property_regions = ['강남구', '서초구', '송파구', '마포구', '용산구']
        property_names = ['아파트', '오피스텔', '상가', '빌라', '원룸']

        for i, (region, name) in enumerate(zip(property_regions, property_names)):
            PortfolioHolding.objects.create(
                user=user,
                asset_type='real_estate',
                asset_name=f'{region} {name}',
                ticker='',
                sector_or_region=region,
                currency_code='KRW',
                quantity=1,
                avg_buy_price=Decimal(str(random.uniform(100000000, 1000000000))),
                invested_amount=Decimal(str(random.uniform(100000000, 1000000000))),
                total_buy_amount=Decimal(str(random.uniform(100000000, 1000000000))),
                market_value=Decimal(str(random.uniform(100000000, 1000000000)))
            )
            print(f'부동산 데이터 생성: {region} {name}')

        # 포트폴리오 스냅샷 데이터 생성 (최근 30일)
        for i in range(30):
            date = datetime.now() - timedelta(days=i)
            PortfolioSnapshot.objects.create(
                user=user,
                snapshot_date=date.date(),
                total_value=Decimal(str(random.uniform(10000000, 50000000))),
                total_change=Decimal(str(random.uniform(-1000000, 1000000))),
                total_change_percent=Decimal(str(random.uniform(-5, 5)))
            )

        print('포트폴리오 스냅샷 데이터 생성 완료')
        print(f'총 주식 보유: {PortfolioHolding.objects.filter(user=user, asset_type="stock").count()}개')
        print(f'총 부동산 보유: {PortfolioHolding.objects.filter(user=user, asset_type="real_estate").count()}개')
        print(f'총 스냅샷: {PortfolioSnapshot.objects.filter(user=user).count()}개')
        
    except Exception as e:
        print(f'오류 발생: {e}')

if __name__ == '__main__':
    create_portfolio_data()
