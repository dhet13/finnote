#!/usr/bin/env python
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from dashboard.models import AssetLogUnified, PortfolioHolding
from decimal import Decimal

def update_portfolio_holdings():
    """AssetLogUnified 데이터를 기반으로 PortfolioHolding 업데이트"""
    
    # 모든 사용자의 AssetLogUnified 데이터 가져오기
    logs = AssetLogUnified.objects.all()
    print(f"처리할 로그 수: {logs.count()}")
    
    for log in logs:
        print(f"처리 중: {log.log_id}, {log.asset_type}, {log.asset_name}")
        # 주식 데이터만 처리
        if log.asset_type == 'stock' and log.stock_ticker_symbol:
            # 기존 PortfolioHolding 찾기 또는 생성
            holding, created = PortfolioHolding.objects.get_or_create(
                user_id=log.user_id,
                asset_key=f"stock:{log.stock_ticker_symbol}",
                defaults={
                    'asset_type': 'stock',
                    'stock_ticker_symbol': log.stock_ticker_symbol,
                    'asset_name': log.asset_name or log.stock_ticker_symbol,
                    'sector_or_region': log.sector_or_region or '기타',
                    'currency_code': log.currency_code or 'KRW',
                    'total_quantity': Decimal('0'),
                    'invested_amount': Decimal('0'),
                    'realized_profit': Decimal('0'),
                    'total_buy_amount': Decimal('0'),
                    'total_sell_amount': Decimal('0')
                }
            )
            
            if not created:
                # 기존 데이터 업데이트
                if log.asset_name and not holding.asset_name:
                    holding.asset_name = log.asset_name
                if log.sector_or_region and not holding.sector_or_region:
                    holding.sector_or_region = log.sector_or_region
                holding.save()
            
            print(f"PortfolioHolding 업데이트: {holding.asset_name} ({holding.sector_or_region})")
        
        # 부동산 데이터 처리
        elif log.asset_type == 'real_estate' and log.property_info_id:
            holding, created = PortfolioHolding.objects.get_or_create(
                user_id=log.user_id,
                asset_key=f"re:{log.property_info_id}",
                defaults={
                    'asset_type': 'real_estate',
                    'property_info_id': log.property_info_id,
                    'asset_name': log.asset_name or f"부동산 {log.property_info_id}",
                    'sector_or_region': log.sector_or_region or '기타',
                    'currency_code': log.currency_code or 'KRW',
                    'total_quantity': Decimal('1'),
                    'invested_amount': Decimal('0'),
                    'realized_profit': Decimal('0'),
                    'total_buy_amount': Decimal('0'),
                    'total_sell_amount': Decimal('0')
                }
            )
            
            if not created:
                if log.asset_name and not holding.asset_name:
                    holding.asset_name = log.asset_name
                if log.sector_or_region and not holding.sector_or_region:
                    holding.sector_or_region = log.sector_or_region
                holding.save()
            
            print(f"PortfolioHolding 업데이트: {holding.asset_name} ({holding.sector_or_region})")

if __name__ == '__main__':
    print("PortfolioHolding 업데이트 시작...")
    update_portfolio_holdings()
    print("PortfolioHolding 업데이트 완료!")
