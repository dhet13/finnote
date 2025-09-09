from django.db import migrations

SQL_CREATE = r"""
CREATE VIEW IF NOT EXISTS asset_logs_unified AS
SELECT
  0    AS log_id,
  0    AS user_id,
  'stock' AS asset_type,
  'BUY'   AS action,
  NULL AS stock_ticker_symbol,
  NULL AS property_info_id,
  NULL AS asset_name,
  NULL AS sector_or_region,
  0.0  AS price_per_unit,
  0.0  AS quantity,
  NULL AS fee_amount,
  NULL AS tax_amount,
  0.0  AS total_amount,
  'KRW' AS currency_code,
  NULL AS fx_rate_at_trade,
  CURRENT_TIMESTAMP AS trade_date,
  CURRENT_TIMESTAMP AS created_at,
  NULL AS amount_deposit,
  NULL AS amount_monthly,
  'stub' AS source_table
WHERE 1=0;
"""
SQL_DROP = "DROP VIEW IF EXISTS asset_logs_unified;"

class Migration(migrations.Migration):
    dependencies = [("dashboard", "0006_add_hold_poly_check")]
    operations = [migrations.RunSQL(SQL_CREATE, reverse_sql=SQL_DROP)]
