from django.db import models
from django.conf import settings

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)  
    is_default = models.BooleanField(default=False)  
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tags'
        ordering = ['-is_default', 'created_at']
    
    def __str__(self):
        return f"#{self.name}"

class Post(models.Model):


    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    
    stock_trade_id = models.IntegerField(blank=True, null=True)
    re_deal_id = models.IntegerField(blank=True, null=True)
    
    EMBED_STYLE_CHOICES = [
        ('classic', '클래식'),
        ('compact', '컴팩트'),
    ]
    embed_style = models.CharField(max_length=20, choices=EMBED_STYLE_CHOICES, default='classic')
    embed_payload_json = models.JSONField()
    
    content = models.TextField()
    screenshot_url = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='posts/images/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """매매일지 저장 시 포트폴리오 데이터 자동 업데이트"""
        super().save(*args, **kwargs)
        
        # 매매일지가 거래와 관련된 경우에만 포트폴리오 업데이트
        if self.stock_trade_id or self.re_deal_id:
            self._update_portfolio_data()
    
    def _update_portfolio_data(self):
        """포트폴리오 데이터 업데이트"""
        try:
            from dashboard.models import PortfolioHolding, PortfolioSnapshot
            from decimal import Decimal
            from datetime import date
            
            # 거래 데이터에서 정보 추출
            embed_data = self.embed_payload_json or {}
            
            if self.stock_trade_id:
                # 주식 거래인 경우
                asset_key = f"stock:{embed_data.get('ticker_symbol', '')}"
                asset_name = embed_data.get('stock_name', '')
                sector = embed_data.get('sector', '기타')
                
                # PortfolioHolding 업데이트
                holding, created = PortfolioHolding.objects.get_or_create(
                    user_id=self.user.id,
                    asset_key=asset_key,
                    defaults={
                        'asset_type': 'stock',
                        'stock_ticker_symbol': embed_data.get('ticker_symbol', ''),
                        'asset_name': asset_name,
                        'sector_or_region': sector,
                        'currency_code': embed_data.get('currency_code', 'KRW'),
                        'total_quantity': Decimal('0'),
                        'invested_amount': Decimal('0'),
                        'realized_profit': Decimal('0'),
                        'total_buy_amount': Decimal('0'),
                        'total_sell_amount': Decimal('0')
                    }
                )
                
                if not created:
                    # 기존 데이터 업데이트
                    if asset_name and not holding.asset_name:
                        holding.asset_name = asset_name
                    if sector and not holding.sector_or_region:
                        holding.sector_or_region = sector
                    holding.save()
                
                # PortfolioSnapshot 업데이트
                today = date.today()
                snapshot, created = PortfolioSnapshot.objects.get_or_create(
                    user_id=self.user.id,
                    snapshot_date=today,
                    asset_key=asset_key,
                    defaults={
                        'asset_type': 'stock',
                        'stock_ticker_symbol': embed_data.get('ticker_symbol', ''),
                        'quantity': Decimal('0'),
                        'avg_buy_price': Decimal('0'),
                        'invested_amount': Decimal('0'),
                        'market_price': Decimal('0'),
                        'market_value': Decimal('0'),
                        'currency_code': embed_data.get('currency_code', 'KRW')
                    }
                )
                
            elif self.re_deal_id:
                # 부동산 거래인 경우
                asset_key = f"re:{self.re_deal_id}"
                asset_name = embed_data.get('property_name', f'부동산 {self.re_deal_id}')
                region = embed_data.get('region', '기타')
                
                # PortfolioHolding 업데이트
                holding, created = PortfolioHolding.objects.get_or_create(
                    user_id=self.user.id,
                    asset_key=asset_key,
                    defaults={
                        'asset_type': 'real_estate',
                        'property_info_id': self.re_deal_id,
                        'asset_name': asset_name,
                        'sector_or_region': region,
                        'currency_code': embed_data.get('currency_code', 'KRW'),
                        'total_quantity': Decimal('1'),
                        'invested_amount': Decimal('0'),
                        'realized_profit': Decimal('0'),
                        'total_buy_amount': Decimal('0'),
                        'total_sell_amount': Decimal('0')
                    }
                )
                
                if not created:
                    if asset_name and not holding.asset_name:
                        holding.asset_name = asset_name
                    if region and not holding.sector_or_region:
                        holding.sector_or_region = region
                    holding.save()
                
                # PortfolioSnapshot 업데이트
                today = date.today()
                snapshot, created = PortfolioSnapshot.objects.get_or_create(
                    user_id=self.user.id,
                    snapshot_date=today,
                    asset_key=asset_key,
                    defaults={
                        'asset_type': 'real_estate',
                        'property_info_id': self.re_deal_id,
                        'quantity': Decimal('1'),
                        'avg_buy_price': Decimal('0'),
                        'invested_amount': Decimal('0'),
                        'market_price': Decimal('0'),
                        'market_value': Decimal('0'),
                        'currency_code': embed_data.get('currency_code', 'KRW')
                    }
                )
                
        except Exception as e:
            # 포트폴리오 업데이트 실패해도 매매일지 저장은 계속 진행
            print(f"포트폴리오 데이터 업데이트 실패: {e}")
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'journal_posts'


class Like(models.Model):
    journal = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)  # CREATE_AT
    
    class Meta:
        unique_together = ('journal', 'user')
        db_table = 'likes_table'

class Bookmark(models.Model):
    journal = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='bookmarks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)  # CREATE_AT
    
    class Meta:
        unique_together = ('journal', 'user')
        db_table = 'bookmarks_table'

class Share(models.Model):
    journal = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('journal', 'user')
        db_table = 'shares_table'

class Comment(models.Model):
    journal = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)  # PARENT_ID
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)  # CREATE_AT
    is_edited = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
        db_table = 'comments_table'

class PostReport(models.Model):
    REPORT_REASONS = [
        ('spam', '스팸'),
        ('abuse', '욕설/비방'),
        ('inappropriate', '부적절한 내용'),
        ('fake', '허위 정보'),
        ('other', '기타'),
    ]
    
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_made')
    journal = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reports')
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('reporter', 'journal')
        db_table = 'post_reports_table'

class HiddenPost(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hidden_posts')
    journal = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='hidden_by_users')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'journal')
        db_table = 'hidden_posts_table'