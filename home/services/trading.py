from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional

from django.utils import timezone
from django.utils.dateparse import parse_date

from journals.models import (
    JournalPost,
    REDeal,
    REPropertyInfo,
    StockInfo,
    StockJournal,
    StockTrade,
)

__all__ = [
    "build_embed_payload_from_payload",
    "create_stock_journal_from_embed",
    "create_real_estate_journal_from_embed",
]


def _safe_decimal(value: Any) -> Optional[Decimal]:
    if value in (None, "", {}):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _safe_float(value: Any) -> Optional[float]:
    decimal_value = _safe_decimal(value)
    return float(decimal_value) if decimal_value is not None else None


def _derive_dong(address: Optional[str]) -> str:
    if not address:
        return "-"
    for part in str(address).split():
        if part.endswith("동") or part.endswith("읍") or part.endswith("면"):
            return part
    return "-"


def build_embed_payload_from_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize trading payload from journals modal into a shareable embed structure."""
    if not isinstance(payload, dict):
        return {}

    asset_type = (payload.get("asset_type") or "").lower()

    if not asset_type:
        if payload.get("ticker_symbol"):
            asset_type = "stock"
        elif payload.get("building_name") or payload.get("property_name") or payload.get("sector_or_region"):
            asset_type = "real_estate"

    if asset_type not in {"stock", "real_estate"}:
        return {}

    if asset_type == "stock":
        ticker = (payload.get("ticker_symbol") or "").strip()
        if not ticker:
            return {}

        stock_name = (
            payload.get("stock_name")
            or payload.get("asset_name")
            or payload.get("company_name")
            or ticker
        )
        side = (payload.get("side") or "BUY").upper()
        price = _safe_float(payload.get("price_per_unit") or payload.get("price"))
        quantity = _safe_float(payload.get("quantity"))
        total_amount = _safe_float(payload.get("total_amount"))
        if total_amount is None and price is not None and quantity is not None:
            total_amount = round(price * quantity, 2)

        return {
            "asset_type": "stock",
            "ticker_symbol": ticker,
            "stock_name": stock_name,
            "asset_name": stock_name,
            "side": side,
            "price_per_unit": price,
            "quantity": quantity,
            "total_amount": total_amount,
            "currency_code": payload.get("currency_code") or "KRW",
            "trade_date": payload.get("trade_date"),
            "target_price": _safe_float(payload.get("target_price")),
            "stop_price": _safe_float(payload.get("stop_price")),
            "trade_reason": payload.get("trade_reason"),
        }

    building_name = (
        payload.get("asset_name")
        or payload.get("building_name")
        or payload.get("property_name")
        or "부동산"
    )
    address = (
        payload.get("sector_or_region")
        or payload.get("address_base")
        or payload.get("region")
        or ""
    )
    deal_type = payload.get("deal_type") or "매매"
    total_amount = _safe_float(payload.get("total_amount") or payload.get("amount_main"))
    area_m2 = _safe_float(payload.get("area_m2"))
    price_per_unit = _safe_float(payload.get("price_per_unit"))
    if price_per_unit is None and total_amount is not None and area_m2:
        try:
            price_per_unit = round(total_amount / area_m2, 2)
        except ZeroDivisionError:
            price_per_unit = None

    floor_value = payload.get("floor")
    try:
        floor_int = int(float(floor_value)) if floor_value not in (None, "") else None
    except (TypeError, ValueError):
        floor_int = None

    embed = {
        "asset_type": "real_estate",
        "asset_name": building_name,
        "property_name": building_name,
        "sector_or_region": address,
        "address_base": address,
        "deal_type": deal_type,
        "trade_date": payload.get("trade_date"),
        "total_amount": total_amount,
        "price_per_unit": price_per_unit,
        "quantity": 1,
        "currency_code": payload.get("currency_code") or "KRW",
        "area_m2": area_m2,
        "floor": floor_int,
        "lat": payload.get("lat"),
        "lng": payload.get("lng"),
        "loan_amount": _safe_float(payload.get("loan_amount")),
        "loan_rate": _safe_float(payload.get("loan_rate")),
        "amount_deposit": _safe_float(payload.get("amount_deposit")),
        "amount_monthly": _safe_float(payload.get("amount_monthly")),
        "trade_reason": payload.get("trade_reason"),
        "property_type": payload.get("property_type"),
        "dong": payload.get("dong") or _derive_dong(address),
    }

    return embed


def create_stock_journal_from_embed(user, post, embed_payload):
    ticker = embed_payload.get("ticker_symbol")
    if not ticker or post.stock_trade_id:
        return

    price_decimal = _safe_decimal(embed_payload.get("price_per_unit"))
    quantity_decimal = _safe_decimal(embed_payload.get("quantity"))
    if price_decimal is None or quantity_decimal is None or quantity_decimal <= 0:
        return

    target_decimal = _safe_decimal(embed_payload.get("target_price")) or price_decimal
    stop_decimal = _safe_decimal(embed_payload.get("stop_price")) or Decimal("0")

    trade_date_str = embed_payload.get("trade_date")
    trade_date = parse_date(trade_date_str) if trade_date_str else None
    if trade_date is None:
        trade_date = timezone.now().date()

    stock_info, _ = StockInfo.objects.get_or_create(
        ticker_symbol=ticker,
        defaults={"stock_name": embed_payload.get("stock_name") or ticker},
    )

    # 같은 종목의 기존 journal이 있는지 확인하고, 없으면 새로 생성
    journal, created = StockJournal.objects.get_or_create(
        user=user,
        ticker_symbol=stock_info,
        defaults={
            'target_price': target_decimal,
            'stop_price': stop_decimal,
        }
    )

    # 기존 journal이 있는 경우, target_price와 stop_price를 업데이트 (선택적)
    if not created:
        # 새로운 거래에서 더 의미있는 값이 있다면 업데이트
        if target_decimal and target_decimal != journal.target_price:
            journal.target_price = target_decimal
        if stop_decimal and stop_decimal != journal.stop_price:
            journal.stop_price = stop_decimal
        journal.save()

    trade = StockTrade.objects.create(
        journal=journal,
        user=user,
        ticker_symbol=stock_info,
        side=embed_payload.get("side", "BUY"),
        trade_date=trade_date,
        price_per_share=price_decimal,
        quantity=quantity_decimal,
    )

    JournalPost.objects.create(
        user=user,
        asset_class=JournalPost.AssetClass.STOCK,
        stock_journal=journal,
        title=f"{embed_payload.get('stock_name') or ticker} 매매일지",
        content=post.content,
        visibility=JournalPost.Visibility.PUBLIC,
    )

    embed_payload.setdefault("stock_journal_id", journal.id)
    embed_payload.setdefault("stock_trade_id", trade.id)

    updated_fields = []
    if not post.stock_trade_id:
        post.stock_trade_id = trade.id
        updated_fields.append("stock_trade_id")
    if post.embed_payload_json != embed_payload:
        post.embed_payload_json = embed_payload
        updated_fields.append("embed_payload_json")
    if updated_fields:
        post.save(update_fields=updated_fields)


def create_real_estate_journal_from_embed(user, post, embed_payload):
    if embed_payload.get("asset_type") != "real_estate" or post.re_deal_id:
        return

    address_base = embed_payload.get("address_base") or embed_payload.get("sector_or_region")
    building_name = embed_payload.get("asset_name") or embed_payload.get("property_name")
    if not address_base or not building_name:
        return

    contract_date_str = embed_payload.get("trade_date")
    contract_date = parse_date(contract_date_str) if contract_date_str else None
    if contract_date is None:
        contract_date = timezone.now().date()

    amount_main = _safe_decimal(embed_payload.get("total_amount")) or Decimal("0")
    area_m2 = _safe_decimal(embed_payload.get("area_m2")) or Decimal("0")

    floor_value = embed_payload.get("floor")
    try:
        floor_int = int(float(floor_value)) if floor_value not in (None, "") else 0
    except (TypeError, ValueError):
        floor_int = 0

    lat_decimal = _safe_decimal(embed_payload.get("lat")) or Decimal("0")
    lng_decimal = _safe_decimal(embed_payload.get("lng")) or Decimal("0")
    dong = embed_payload.get("dong") or _derive_dong(address_base)

    property_info, _ = REPropertyInfo.objects.get_or_create(
        address_base=address_base,
        building_name=building_name,
        defaults={
            "property_type": embed_payload.get("property_type") or "apartment",
            "lawd_cd": embed_payload.get("lawd_cd"),
            "dong": dong,
            "lat": lat_decimal,
            "lng": lng_decimal,
        },
    )

    deal = REDeal.objects.create(
        user=user,
        property_info=property_info,
        deal_type=embed_payload.get("deal_type") or REDeal.DealType.BUY_SELL,
        contract_date=contract_date,
        amount_main=amount_main,
        amount_deposit=_safe_decimal(embed_payload.get("amount_deposit")) or Decimal("0"),
        amount_monthly=_safe_decimal(embed_payload.get("amount_monthly")) or Decimal("0"),
        area_m2=area_m2,
        floor=floor_int,
        loan_amount=_safe_decimal(embed_payload.get("loan_amount")),
        loan_rate=_safe_decimal(embed_payload.get("loan_rate")),
        fees_broker=_safe_decimal(embed_payload.get("fees_broker")),
        tax_acq=_safe_decimal(embed_payload.get("tax_acq")),
        reg_fee=_safe_decimal(embed_payload.get("reg_fee")),
        misc_cost=_safe_decimal(embed_payload.get("misc_cost")),
    )

    JournalPost.objects.create(
        user=user,
        asset_class=JournalPost.AssetClass.REAL_ESTATE,
        re_deal=deal,
        title=f"{building_name} 부동산 거래",
        content=post.content,
        visibility=JournalPost.Visibility.PUBLIC,
    )

    embed_payload.setdefault("property_info_id", property_info.property_info_id)
    embed_payload.setdefault("re_deal_id", deal.id)

    updated_fields = []
    if not post.re_deal_id:
        post.re_deal_id = deal.id
        updated_fields.append("re_deal_id")
    if post.embed_payload_json != embed_payload:
        post.embed_payload_json = embed_payload
        updated_fields.append("embed_payload_json")
    if updated_fields:
        post.save(update_fields=updated_fields)
