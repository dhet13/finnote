#!/usr/bin/env python
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from home.models import Post
from dashboard.models import PortfolioHolding, PortfolioSnapshot
from decimal import Decimal
from datetime import date

def sync_existing_posts():
    """기존 매매일지 데이터를 기반으로 포트폴리오 데이터 동기화"""
    
    # 거래와 관련된 매매일지만 처리
    posts = Post.objects.filter(
        models.Q(stock_trade_id__isnull=False) | models.Q(re_deal_id__isnull=False)
    )
    
    print(f"처리할 매매일지 수: {posts.count()}")
    
    for post in posts:
        print(f"처리 중: Post ID {post.id}, stock_trade_id: {post.stock_trade_id}, re_deal_id: {post.re_deal_id}")
        
        try:
            # Post 모델의 _update_portfolio_data 메서드 호출
            post._update_portfolio_data()
            print(f"  ✓ 포트폴리오 데이터 업데이트 완료")
        except Exception as e:
            print(f"  ✗ 포트폴리오 데이터 업데이트 실패: {e}")
    
    print("기존 매매일지 동기화 완료!")

if __name__ == '__main__':
    from django.db import models
    sync_existing_posts()

