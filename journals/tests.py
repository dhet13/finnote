from django.test import TestCase, Client
from decimal import Decimal
from django.contrib.auth import get_user_model
from .models import StockInfo, StockJournal, StockTrade, JournalPost, REDeal, REPropertyInfo
import json

# Per prompt_master.md:
# 단위테스트:
#  · 집계 로직(평단/손익/상태)
#  · 부동산 실거래 정규화
#  · /journals/compose/?modal=1는 partial, 쿼리 없음은 페이지 렌더

class JournalViewTests(TestCase):
    def test_compose_view_full_page(self):
        """GET /journals/compose/ renders the full page template."""
        response = self.client.get('/journals/compose/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'compose_page_clean.html')

    def test_compose_view_modal_partial(self):
        """GET /journals/compose/?modal=1 renders the modal partial template."""
        response = self.client.get('/journals/compose/?modal=1')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, '_compose_modal.html')

class StockJournalAggregationTests(TestCase):
    def setUp(self):
        """Set up a user, stock, and journal for aggregation tests."""
        User = get_user_model()
        self.user = User.objects.create_user(
            my_ID='testuser',
            email='testuser@example.com',
            password='password123',
            nickname='testnickname'
        )
        self.stock_info = StockInfo.objects.create(
            ticker_symbol='005930.KS',
            stock_name='Samsung Electronics'
        )
        self.journal = StockJournal.objects.create(
            user=self.user,
            ticker_symbol=self.stock_info,
            target_price=Decimal('80000'),
            stop_price=Decimal('60000')
        )

    def test_avg_buy_price_calculation(self):
        """Tests the calculation of average buy price."""
        StockTrade.objects.create(
            journal=self.journal, user=self.user, ticker_symbol=self.stock_info,
            side=StockTrade.Side.BUY, trade_date='2025-01-01',
            price_per_share=Decimal('70000'), quantity=Decimal('10')
        )
        StockTrade.objects.create(
            journal=self.journal, user=self.user, ticker_symbol=self.stock_info,
            side=StockTrade.Side.BUY, trade_date='2025-01-02',
            price_per_share=Decimal('72000'), quantity=Decimal('5')
        )
        self.journal.refresh_from_db()
        # Expected: (70000 * 10 + 72000 * 5) / (10 + 5) = 1060000 / 15 = 70666.6667
        self.assertAlmostEqual(self.journal.avg_buy_price, Decimal('70666.6667'), places=4)

    def test_realized_pnl_and_status_change_on_full_sell(self):
        """Tests realized PnL and status change to 'completed' on a full sell-off."""
        StockTrade.objects.create(
            journal=self.journal, user=self.user, ticker_symbol=self.stock_info,
            side=StockTrade.Side.BUY, trade_date='2025-01-01',
            price_per_share=Decimal('70000'), quantity=Decimal('10')
        )
        self.journal.refresh_from_db()
        self.assertEqual(self.journal.status, StockJournal.Status.OPEN)
        self.assertIsNone(self.journal.realized_pnl)

        StockTrade.objects.create(
            journal=self.journal, user=self.user, ticker_symbol=self.stock_info,
            side=StockTrade.Side.SELL, trade_date='2025-01-05',
            price_per_share=Decimal('75000'), quantity=Decimal('10')
        )
        self.journal.refresh_from_db()
        self.assertEqual(self.journal.status, StockJournal.Status.COMPLETED)
        self.assertIsNotNone(self.journal.realized_pnl)
        self.assertAlmostEqual(self.journal.realized_pnl, Decimal('50000.00'), places=2)

    def test_status_and_pnl_on_partial_sell(self):
        """Tests that status remains 'open' and PnL is null on a partial sell."""
        StockTrade.objects.create(
            journal=self.journal, user=self.user, ticker_symbol=self.stock_info,
            side=StockTrade.Side.BUY, trade_date='2025-01-01',
            price_per_share=Decimal('70000'), quantity=Decimal('10')
        )
        StockTrade.objects.create(
            journal=self.journal, user=self.user, ticker_symbol=self.stock_info,
            side=StockTrade.Side.SELL, trade_date='2025-01-05',
            price_per_share=Decimal('75000'), quantity=Decimal('5')
        )
        self.journal.refresh_from_db()
        self.assertEqual(self.journal.status, StockJournal.Status.OPEN)
        self.assertIsNone(self.journal.realized_pnl, "PnL should be null for open journals")

class JournalAPITests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            my_ID='apiuser',
            email='apiuser@example.com',
            password='password123',
            nickname='apinickname'
        )
        self.stock_info = StockInfo.objects.create(
            ticker_symbol='000660.KS',
            stock_name='SK Hynix'
        )

    def test_create_stock_journal_api_unauthenticated(self):
        response = self.client.post('/api/stock/journals/', data={}, content_type='application/json')
        self.assertEqual(response.status_code, 302)

    def test_create_stock_journal_api_success(self):
        self.client.login(my_ID='apiuser', password='password123')
        payload = {
            "ticker_symbol": self.stock_info.ticker_symbol,
            "title": "SK Hynix Long Term",
            "content": "Entering a position based on AI hype.",
            "visibility": "public",
            "target_price": 200000,
            "stop_price": 120000,
            "legs": [
                {"side": "BUY", "date": "2025-01-01", "price_per_share": 150000, "quantity": 10},
                {"side": "BUY", "date": "2025-01-02", "price_per_share": 152000, "quantity": 5}
            ]
        }
        response = self.client.post('/api/stock/journals/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(StockJournal.objects.filter(user=self.user, ticker_symbol=self.stock_info).exists())
        self.assertEqual(StockTrade.objects.count(), 2)
        self.assertTrue(JournalPost.objects.filter(title="SK Hynix Long Term").exists())
        response_data = response.json()
        self.assertIn('post_id', response_data)
        self.assertEqual(response_data['journal_status'], 'open')
        journal = StockJournal.objects.first()
        self.assertAlmostEqual(journal.avg_buy_price, Decimal('150666.6667'), places=4)

    def test_delete_journal_post_api_success(self):
        self.client.login(my_ID='apiuser', password='password123')
        journal = StockJournal.objects.create(
            user=self.user, ticker_symbol=self.stock_info, target_price=1, stop_price=1
        )
        StockTrade.objects.create(
            journal=journal, user=self.user, ticker_symbol=self.stock_info,
            side='BUY', trade_date='2025-01-01', price_per_share=100, quantity=10
        )
        post = JournalPost.objects.create(
            user=self.user, stock_journal=journal, asset_class='stock', title='to be deleted'
        )
        self.assertEqual(JournalPost.objects.count(), 1)
        response = self.client.delete(f'/api/journal-posts/{post.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(JournalPost.objects.count(), 0)
        self.assertEqual(StockJournal.objects.count(), 0)
        self.assertEqual(StockTrade.objects.count(), 0)

    def test_delete_journal_post_unauthorized(self):
        journal = StockJournal.objects.create(
            user=self.user, ticker_symbol=self.stock_info, target_price=1, stop_price=1
        )
        post = JournalPost.objects.create(
            user=self.user, stock_journal=journal, asset_class='stock', title='owned post'
        )
        other_user = get_user_model().objects.create_user(
            my_ID='otheruser', email='other@e.com', password='password', nickname='other'
        )
        self.client.login(my_ID='otheruser', password='password')
        response = self.client.delete(f'/api/journal-posts/{post.id}/')
        self.assertEqual(response.status_code, 404)
        self.assertTrue(JournalPost.objects.filter(pk=post.id).exists())

    def test_get_posts_api_feed(self):
        # Mock yfinance to avoid real network calls in tests
        from unittest import mock
        with mock.patch('yfinance.Tickers') as mock_tickers:
            # Configure the mock to return some data
            mock_ticker_obj = mock.Mock()
            mock_ticker_obj.fast_info = {'lastPrice': 160000}
            mock_tickers.return_value.tickers = {self.stock_info.ticker_symbol: mock_ticker_obj}

            JournalPost.objects.create(
                user=self.user, asset_class='stock', title='Public Post',
                stock_journal=StockJournal.objects.create(
                    user=self.user, ticker_symbol=self.stock_info, target_price=170000, stop_price=140000
                ),
                visibility=JournalPost.Visibility.PUBLIC
            )
            JournalPost.objects.create(
                user=self.user, asset_class='stock', title='Private Post',
                stock_journal=StockJournal.objects.create(
                    user=self.user, ticker_symbol=self.stock_info, target_price=1, stop_price=1
                ),
                visibility=JournalPost.Visibility.PRIVATE
            )

            response = self.client.get('/api/posts/')
            self.assertEqual(response.status_code, 200)
            response_data = response.json()
            self.assertEqual(len(response_data['posts']), 1)
            first_post = response_data['posts'][0]
            self.assertEqual(first_post['title'], 'Public Post')
            self.assertEqual(first_post['asset_details']['signal'], 'yellow')