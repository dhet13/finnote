from django.db import migrations

SQL_CREATE = r"""
CREATE VIEW IF NOT EXISTS asset_logs_unified AS
-- 주식 거래 로그
SELECT
  st.id AS log_id,
  st.user_id AS user_id,
  'stock' AS asset_type,
  st.side AS action,
  st.ticker_symbol_id AS stock_ticker_symbol,
  NULL AS property_info_id,
  si.stock_name AS asset_name,
  si.sector AS sector_or_region,
  st.price_per_share AS price_per_unit,
  st.quantity AS quantity,
  st.fee_amount AS fee_amount,
  st.tax_amount AS tax_amount,
  (st.price_per_share * st.quantity + COALESCE(st.fee_amount, 0) + COALESCE(st.tax_amount, 0)) AS total_amount,
  COALESCE(si.currency, 'KRW') AS currency_code,
  NULL AS fx_rate_at_trade,
  st.trade_date AS trade_date,
  st.created_at AS created_at,
  NULL AS amount_deposit,
  NULL AS amount_monthly,
  'journals_stocktrade' AS source_table
FROM journals_stocktrade st
LEFT JOIN journals_stockinfo si ON st.ticker_symbol_id = si.ticker_symbol

UNION ALL

-- 부동산 거래 로그  
SELECT
  rd.id AS log_id,
  rd.user_id AS user_id,
  'real_estate' AS asset_type,
  CASE rd.deal_type 
    WHEN '매매' THEN 'BUY'
    WHEN '전세' THEN 'LEASE'
    WHEN '월세' THEN 'RENT'
  END AS action,
  NULL AS stock_ticker_symbol,
  rd.property_info_id AS property_info_id,
  rp.building_name AS asset_name,
  rp.dong AS sector_or_region,
  rd.amount_main AS price_per_unit,
  1.0 AS quantity,
  (COALESCE(rd.fees_broker, 0) + COALESCE(rd.reg_fee, 0) + COALESCE(rd.misc_cost, 0)) AS fee_amount,
  rd.tax_acq AS tax_amount,
  (rd.amount_main + COALESCE(rd.fees_broker, 0) + COALESCE(rd.tax_acq, 0) + COALESCE(rd.reg_fee, 0) + COALESCE(rd.misc_cost, 0)) AS total_amount,
  'KRW' AS currency_code,
  NULL AS fx_rate_at_trade,
  rd.contract_date AS trade_date,
  rd.created_at AS created_at,
  rd.amount_deposit AS amount_deposit,
  rd.amount_monthly AS amount_monthly,
  'journals_redeal' AS source_table
FROM journals_redeal rd
LEFT JOIN journals_repropertyinfo rp ON rd.property_info_id = rp.property_info_id;
"""
SQL_DROP = "DROP VIEW IF EXISTS asset_logs_unified;"

class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0006_add_hold_poly_check"),
        ("journals", "0001_initial")
    ]
    operations = [migrations.RunSQL(SQL_CREATE, reverse_sql=SQL_DROP)]
