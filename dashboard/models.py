from django.db import models
from locale import currency
from typing import Text, assert_type
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, CheckConstraint



class AssetLogUnified(models.Model):
    log_id = models.BigIntegerField(primary_key=True)
    user_id = models.BigIntegerField()
    asset_type = models.CharField(max_length=20)           # 'stock' | 'real_estate'
    action = models.CharField(max_length=10)               # 'BUY' | 'SELL' | 'LEASE' | 'RENT'
    stock_ticker_symbol = models.TextField(null=True, blank=True)
    property_info_id = models.BigIntegerField(null=True, blank=True)
    asset_name = models.TextField(null=True, blank=True)
    sector_or_region = models.TextField(null=True, blank=True)
    price_per_unit = models.DecimalField(max_digits=20, decimal_places=6)
    quantity = models.DecimalField(max_digits=20, decimal_places=6)
    fee_amount = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=20, decimal_places=6)
    currency_code = models.CharField(max_length=3)
    fx_rate_at_trade = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    trade_date = models.DateTimeField()
    created_at = models.DateTimeField()
    amount_deposit = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    amount_monthly = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    source_table = models.TextField()

    class Meta:
        managed = False                 # ✅ 뷰/머뷰는 Django가 생성/수정 안 함
        db_table = "asset_logs_unified" # 뷰 이름과 동일
        ordering = ["-trade_date"]


class PortfolioHolding(models.Model):
    user_id = models.BigIntegerField()
    asset_type = models.CharField(max_length=20)  # 'stock'|'real_estate'
    stock_ticker_symbol = models.TextField(null=True, blank=True)
    property_info_id = models.BigIntegerField(null=True, blank=True)

    # 🔑 폴리모픽 단일 키 (예: stock:AAPL / re:12345)
    asset_key = models.TextField(editable=False, db_index=True)
    asset_name = models.TextField(null=True, blank=True)
    sector_or_region = models.TextField(null=True, blank=True)
    currency_code = models.CharField(max_length=3, default="KRW")

    total_quantity = models.DecimalField(max_digits=20, decimal_places=6, default=0)
    avg_buy_price  = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    invested_amount = models.DecimalField(max_digits=20, decimal_places=6, default=0)
    realized_profit = models.DecimalField(max_digits=20, decimal_places=6, default=0)
    total_buy_amount  = models.DecimalField(max_digits=20, decimal_places=6, default=0)
    total_sell_amount = models.DecimalField(max_digits=20, decimal_places=6, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # 정확히 하나의 키만 채워지도록 앱 레벨 검증
        s, r = self.stock_ticker_symbol, self.property_info_id
        assert (bool(s) ^ bool(r)), "stock_ticker_symbol 또는 property_info_id 중 하나만 입력하세요."
        self.asset_key = f"stock:{s}" if s else f"re:{r}"

    def save(self, *a, **kw):
        if self.stock_ticker_symbol and not self.property_info_id:
            self.asset_key = f"stock:{self.stock_ticker_symbol}"
        elif self.property_info_id and not self.stock_ticker_symbol:
            self.asset_key = f"re:{self.property_info_id}"
        else:
            raise ValueError("stock_ticker_symbol 또는 property_info_id 중 하나만 입력하세요.")
        return super().save(*a, **kw)

    class Meta:
        unique_together = [("user_id", "asset_key")]
        indexes = [
            models.Index(fields=["user_id"]),
            models.Index(fields=["user_id", "sector_or_region"]),
        ]
        constraints = [
            # 유저별 자산 1행 보장(조건부 유니크)
            models.UniqueConstraint(
                fields=["user_id","stock_ticker_symbol"],
                condition=Q(asset_type="stock"),
                name="ux_hold_stock"
            ),
            models.UniqueConstraint(
                fields=["user_id","property_info_id"],
                condition=Q(asset_type="real_estate"),
                name="ux_hold_re"
            ),
            # 주식 키/부동산 키 중 정확히 하나만 채워져야 함
            models.CheckConstraint(
                check=Q(asset_type="stock", stock_ticker_symbol__isnull=False, property_info_id__isnull=True)
                   | Q(asset_type="real_estate", property_info_id__isnull=False, stock_ticker_symbol__isnull=True),
                name="chk_hold_polykey"
            ),
        ]

class PortfolioSnapshot(models.Model):
    user_id = models.BigIntegerField()
    snapshot_date = models.DateField()
    asset_type = models.CharField(max_length=20)
    stock_ticker_symbol = models.TextField(null=True, blank=True)
    property_info_id = models.BigIntegerField(null=True, blank=True)

    # 🔑 임시 단계: NULL 허용
    asset_key = models.TextField(editable=False, db_index=True)

    quantity = models.DecimalField(max_digits=20, decimal_places=6)
    avg_buy_price = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    invested_amount = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    market_price = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    market_value = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    currency_code = models.CharField(max_length=3, default="KRW")

    def clean(self):
        s, r = self.stock_ticker_symbol, self.property_info_id
        # 정확히 하나만 채워졌는지 앱 레벨 검증
        if bool(s) == bool(r):
            raise ValueError("stock_ticker_symbol 또는 property_info_id 중 하나만 입력하세요.")
        self.asset_key = f"stock:{s}" if s else f"re:{r}"

    def save(self, *a, **kw):
        if self.stock_ticker_symbol and not self.property_info_id:
            self.asset_key = f"stock:{self.stock_ticker_symbol}"
        elif self.property_info_id and not self.stock_ticker_symbol:
            self.asset_key = f"re:{self.property_info_id}"
        else:
            raise ValueError("stock_ticker_symbol 또는 property_info_id 중 하나만 입력하세요.")
        return super().save(*a, **kw)

    class Meta:
        # SQLite용: partial unique 대신 단일 키로 유니크
        unique_together = [("user_id", "snapshot_date", "asset_key")]
        indexes = [models.Index(fields=["user_id", "snapshot_date"])]
        constraints = [
            CheckConstraint(
                check=Q(stock_ticker_symbol__isnull=False, property_info_id__isnull=True) |
                      Q(stock_ticker_symbol__isnull=True,  property_info_id__isnull=False),
                name="chk_snap_poly_exactly_one_key",
            ),
        ]