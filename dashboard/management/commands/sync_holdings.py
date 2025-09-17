# dashboard/management/commands/sync_holdings.py
from django.core.management.base import BaseCommand
from django.db import transaction
from journals.models import StockTrade
from dashboard.models import PortfolioHolding, PortfolioSnapshot
from dashboard.views.services import process_trade_for_portfolio

class Command(BaseCommand):
    help = 'Rebuilds the entire portfolio history (holdings and snapshots) from trades.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Rebuilding portfolio data from scratch...')

        # 1. Clear existing portfolio data
        self.stdout.write('Deleting existing PortfolioHolding and PortfolioSnapshot data...')
        deleted_snapshots, _ = PortfolioSnapshot.objects.all().delete()
        deleted_holdings, _ = PortfolioHolding.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_snapshots} snapshots and {deleted_holdings} holdings.'))

        # 2. Get all trades in chronological order
        trades = StockTrade.objects.order_by('trade_date', 'created_at').values_list('id', flat=True)
        total_trades = len(trades)

        if total_trades == 0:
            self.stdout.write(self.style.SUCCESS('No trades found to process.'))
            return

        self.stdout.write(f'Found {total_trades} trades to process.')

        # 3. Process each trade
        for i, trade_id in enumerate(trades):
            self.stdout.write(f'Processing trade {i + 1}/{total_trades} (ID: {trade_id})...')
            try:
                process_trade_for_portfolio(trade_id)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Error processing trade {trade_id}: {e}'))

        self.stdout.write(self.style.SUCCESS('Successfully rebuilt all portfolio data.'))