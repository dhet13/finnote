from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

# Per prompt_master.md:
# enums via CharField(choices=...), timezone-aware DateTime (USE_TZ=True),
# FKs use settings.AUTH_USER_MODEL, JSONField for snapshots, Decimal for money.


class StockInfo(models.Model):
    ticker_symbol = models.CharField(max_length=20, primary_key=True)
    stock_name = models.CharField(max_length=255)
    sector = models.CharField(max_length=100, blank=True, null=True)
    exchange = models.CharField(max_length=50, blank=True, null=True)
    currency = models.CharField(max_length=10, blank=True, null=True)
    last_close_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.stock_name} ({self.ticker_symbol})"


class StockJournal(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        COMPLETED = 'completed', 'Completed'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stock_journals')
    ticker_symbol = models.ForeignKey(StockInfo, on_delete=models.PROTECT, related_name='journals')

    target_price = models.DecimalField(max_digits=18, decimal_places=4)
    stop_price = models.DecimalField(max_digits=18, decimal_places=4)

    total_buy_qty = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0.0'))
    total_sell_qty = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0.0'))

    avg_buy_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    avg_sell_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)

    net_qty = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0.0'))
    realized_pnl = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'ticker_symbol']),
        ]


class StockTrade(models.Model):
    class Side(models.TextChoices):
        BUY = 'BUY', 'Buy'
        SELL = 'SELL', 'Sell'

    journal = models.ForeignKey(StockJournal, on_delete=models.CASCADE, related_name='trades')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stock_trades')
    ticker_symbol = models.ForeignKey(StockInfo, on_delete=models.PROTECT, related_name='trades')

    side = models.CharField(max_length=4, choices=Side.choices)
    trade_date = models.DateField()

    price_per_share = models.DecimalField(max_digits=18, decimal_places=4)
    quantity = models.DecimalField(max_digits=18, decimal_places=6)

    fee_rate = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    tax_rate = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    fee_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['journal', 'trade_date']),
        ]


class REPropertyInfo(models.Model):
    property_info_id = models.AutoField(primary_key=True)
    property_type = models.CharField(max_length=50)
    building_name = models.CharField(max_length=255)
    address_base = models.CharField(max_length=255)
    lawd_cd = models.CharField(max_length=5)  # 법정동 코드
    dong = models.CharField(max_length=50)
    build_year = models.IntegerField(null=True, blank=True)
    lat = models.DecimalField(max_digits=10, decimal_places=7)  # Latitude
    lng = models.DecimalField(max_digits=10, decimal_places=7)  # Longitude
    total_floor = models.IntegerField(null=True, blank=True)
    total_units = models.IntegerField(null=True, blank=True)
    exclusive_types = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.building_name} ({self.address_base})"


class REDeal(models.Model):
    class DealType(models.TextChoices):
        BUY_SELL = '매매', '매매'
        JEONSE = '전세', '전세'
        WOLSE = '월세', '월세'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='re_deals')
    property_info = models.ForeignKey(REPropertyInfo, on_delete=models.PROTECT, related_name='deals')

    deal_type = models.CharField(max_length=10, choices=DealType.choices)
    contract_date = models.DateField()

    amount_main = models.DecimalField(max_digits=18, decimal_places=0)  # 매매가/전세가/보증금
    amount_deposit = models.DecimalField(max_digits=18, decimal_places=0, default=0)  # 보증금
    amount_monthly = models.DecimalField(max_digits=18, decimal_places=0, default=0)  # 월세

    area_m2 = models.DecimalField(max_digits=8, decimal_places=2)  # 전용면적
    floor = models.IntegerField()

    loan_amount = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    loan_rate = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    fees_broker = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    tax_acq = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    reg_fee = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    misc_cost = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)

    raw_snapshot_json = models.JSONField(default=dict)
    snapshot_source = models.CharField(max_length=20, blank=True)
    snapshot_fetched_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'property_info']),
            models.Index(fields=['contract_date']),
        ]


class JournalPost(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = 'public', 'Public'
        PRIVATE = 'private', 'Private'

    class AssetClass(models.TextChoices):
        STOCK = 'stock', 'Stock'
        REAL_ESTATE = 'realestate', 'Real Estate'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='journal_posts')
    visibility = models.CharField(max_length=10, choices=Visibility.choices, default=Visibility.PUBLIC)

    asset_class = models.CharField(max_length=10, choices=AssetClass.choices)
    stock_journal = models.ForeignKey(StockJournal, on_delete=models.CASCADE, null=True, blank=True, related_name='posts')
    re_deal = models.ForeignKey(REDeal, on_delete=models.CASCADE, null=True, blank=True, related_name='posts')

    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    screenshot_url = models.URLField(max_length=2000, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'visibility', 'created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                name='stock_journal_or_re_deal_is_set',
                check=(
                    models.Q(asset_class='stock', stock_journal__isnull=False, re_deal__isnull=True)
                    | models.Q(asset_class='realestate', re_deal__isnull=False, stock_journal__isnull=True)
                ),
            )
        ]

