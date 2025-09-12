from django.core.management.base import BaseCommand
from journals.models import StockInfo

class Command(BaseCommand):
    help = 'Populates the StockInfo table with sample data.'

    def handle(self, *args, **options):
        stocks = [
            {'ticker_symbol': '005930.KS', 'stock_name': 'Samsung Electronics', 'exchange': 'KOSPI', 'currency': 'KRW'},
            {'ticker_symbol': 'AAPL', 'stock_name': 'Apple Inc.', 'exchange': 'NASDAQ', 'currency': 'USD'},
            {'ticker_symbol': 'GOOGL', 'stock_name': 'Alphabet Inc. (GOOGL)', 'exchange': 'NASDAQ', 'currency': 'USD'},
            {'ticker_symbol': 'MSFT', 'stock_name': 'Microsoft Corp.', 'exchange': 'NASDAQ', 'currency': 'USD'},
        ]

        self.stdout.write('Populating StockInfo table...')
        for stock_data in stocks:
            obj, created = StockInfo.objects.get_or_create(
                ticker_symbol=stock_data['ticker_symbol'],
                defaults={
                    'stock_name': stock_data['stock_name'],
                    'exchange': stock_data['exchange'],
                    'currency': stock_data['currency']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created {obj.stock_name} ({obj.ticker_symbol})'))
            else:
                self.stdout.write(self.style.WARNING(f'{obj.stock_name} ({obj.ticker_symbol}) already exists.'))
        self.stdout.write(self.style.SUCCESS('StockInfo population complete.'))
