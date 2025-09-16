#!/usr/bin/env python
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from dashboard.models import PortfolioHolding
from accounts.models import User

def check_stock_data():
    try:
        user = User.objects.get(id=1)
        stock_holdings = PortfolioHolding.objects.filter(user=user, asset_type='stock').order_by('sector_or_region', 'asset_name')

        print('=== 주식 포트폴리오 데이터 ===')
        print(f'총 주식 종목 수: {stock_holdings.count()}개')
        print()

        for holding in stock_holdings:
            print(f'종목명: {holding.asset_name}')
            print(f'  티커: {holding.ticker}')
            print(f'  섹터: {holding.sector_or_region}')
            print(f'  수량: {holding.quantity}주')
            print(f'  평균 매수가: {holding.avg_buy_price:,}원')
            print(f'  시장가치: {holding.market_value:,}원')
            print(f'  통화: {holding.currency_code}')
            print('-' * 50)
            
        print()
        print('=== 섹터별 요약 ===')
        sectors = {}
        for holding in stock_holdings:
            sector = holding.sector_or_region
            if sector not in sectors:
                sectors[sector] = {'count': 0, 'total_value': 0}
            sectors[sector]['count'] += 1
            sectors[sector]['total_value'] += float(holding.market_value)
        
        for sector, data in sectors.items():
            print(f'{sector}: {data["count"]}개 종목, 총 가치: {data["total_value"]:,.0f}원')
            
    except Exception as e:
        print(f'오류 발생: {e}')

if __name__ == '__main__':
    check_stock_data()
