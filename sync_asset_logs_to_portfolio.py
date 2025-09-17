#!/usr/bin/env python
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from dashboard.models import AssetLogUnified, PortfolioHolding, PortfolioSnapshot
from decimal import Decimal
from datetime import date

def sync_asset_logs_to_portfolio():
    """AssetLogUnified 데이터를 PortfolioHolding과 PortfolioSnapshot으로 동기화"""
    
    # AssetLogUnified에서 모든 데이터 가져오기
    logs = AssetLogUnified.objects.all()
    print(f"처리할 AssetLogUnified 데이터 수: {logs.count()}")
    
    for log in logs:
        print(f"처리 중: {log.log_id}, {log.asset_type}, {log.asset_name}, user_id: {log.user_id}")
        
        try:
            if log.asset_type == 'stock' and log.stock_ticker_symbol:
                # 주식 데이터 처리
                asset_key = f"stock:{log.stock_ticker_symbol}"
                
                # PortfolioHolding 생성/업데이트
                holding, created = PortfolioHolding.objects.get_or_create(
                    user_id=log.user_id,
                    asset_key=asset_key,
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
                
                print(f"  ✓ PortfolioHolding 업데이트: {holding.asset_name} ({holding.sector_or_region})")
                
                # PortfolioSnapshot 생성/업데이트
                today = date.today()
                snapshot, created = PortfolioSnapshot.objects.get_or_create(
                    user_id=log.user_id,
                    snapshot_date=today,
                    asset_key=asset_key,
                    defaults={
                        'asset_type': 'stock',
                        'stock_ticker_symbol': log.stock_ticker_symbol,
                        'quantity': Decimal('0'),
                        'avg_buy_price': Decimal('0'),
                        'invested_amount': Decimal('0'),
                        'market_price': Decimal('0'),
                        'market_value': Decimal('0'),
                        'currency_code': log.currency_code or 'KRW'
                    }
                )
                
                print(f"  ✓ PortfolioSnapshot 업데이트: {snapshot.asset_key}")
                
            elif log.asset_type == 'real_estate' and log.property_info_id:
                # 부동산 데이터 처리
                asset_key = f"re:{log.property_info_id}"
                
                # PortfolioHolding 생성/업데이트
                holding, created = PortfolioHolding.objects.get_or_create(
                    user_id=log.user_id,
                    asset_key=asset_key,
                    defaults={
                        'asset_type': 'real_estate',
                        'property_info_id': log.property_info_id,
                        'asset_name': log.asset_name or f'부동산 {log.property_info_id}',
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
                
                print(f"  ✓ PortfolioHolding 업데이트: {holding.asset_name} ({holding.sector_or_region})")
                
                # PortfolioSnapshot 생성/업데이트
                today = date.today()
                snapshot, created = PortfolioSnapshot.objects.get_or_create(
                    user_id=log.user_id,
                    snapshot_date=today,
                    asset_key=asset_key,
                    defaults={
                        'asset_type': 'real_estate',
                        'property_info_id': log.property_info_id,
                        'quantity': Decimal('1'),
                        'avg_buy_price': Decimal('0'),
                        'invested_amount': Decimal('0'),
                        'market_price': Decimal('0'),
                        'market_value': Decimal('0'),
                        'currency_code': log.currency_code or 'KRW'
                    }
                )
                
                print(f"  ✓ PortfolioSnapshot 업데이트: {snapshot.asset_key}")
                
        except Exception as e:
            print(f"  ✗ 오류 발생: {e}")
    
    print("AssetLogUnified → PortfolioHolding/PortfolioSnapshot 동기화 완료!")

if __name__ == '__main__':
    sync_asset_logs_to_portfolio()

