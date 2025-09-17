from django.core.management.base import BaseCommand
from journals.models import StockInfo
import yfinance as yf

class Command(BaseCommand):
    help = 'Updates stock information from yfinance'

    def handle(self, *args, **options):
        self.stdout.write('Starting stock info update...')
        for stock_info in StockInfo.objects.all():
            try:
                ticker = yf.Ticker(stock_info.ticker_symbol)
                info = ticker.info
                
                new_name = info.get('longName', stock_info.ticker_symbol)
                new_currency = info.get('currency', 'KRW').upper()

                if stock_info.stock_name != new_name or stock_info.currency != new_currency:
                    stock_info.stock_name = new_name
                    stock_info.currency = new_currency
                    stock_info.save()
                    self.stdout.write(self.style.SUCCESS(f'Successfully updated {stock_info.ticker_symbol}'))
                else:
                    self.stdout.write(f'No update needed for {stock_info.ticker_symbol}')

            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Failed to update {stock_info.ticker_symbol}: {e}'))

        self.stdout.write(self.style.SUCCESS('Stock info update complete.'))
