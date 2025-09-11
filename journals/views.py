from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from django.utils.dateparse import parse_date
from django.db import transaction
from decimal import Decimal

from decouple import config
import json
import requests
import yfinance as yf

from .models import (
    StockInfo, StockJournal, StockTrade,
    REPropertyInfo, REDeal, JournalPost
)


# Page Views
def compose(request):
    """
    Renders the compose page or a modal partial.
    GET /journals/compose/
    - modal=1 -> _compose_modal.html
    - no query -> compose_page.html
    """
    if request.GET.get('modal') == '1':
        template_name = '_compose_modal.html'
    else:
        template_name = 'compose_page_clean.html'

    asset_type = request.GET.get('asset', 'stock')
    return render(request, template_name, {'asset_type': asset_type})


@login_required
def my_journal_list(request):
    """
    Renders a page with a list of the current user's journal posts.
    """
    journal_posts = JournalPost.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'journal_posts': journal_posts,
    }
    return render(request, 'my_journal_list.html', context)


@require_http_methods(["GET"])
def stock_card_details_api(request, ticker):
    """
    GET /api/stock/<ticker>/card-details/
    Returns all data needed for the stock selection card component.
    """
    if not ticker:
        return JsonResponse({'error': 'Ticker symbol is required.'}, status=400)

    try:
        t = yf.Ticker(ticker)

        # Using 'fast_info' is quicker than history for current price
        info = t.fast_info
        last_close = info.get('lastPrice')
        prev_close = info.get('previousClose')
        stock_name = info.get('longName', ticker.upper())

        if last_close is None or prev_close is None:
            # Fallback to history if fast_info is not enough
            hist_2d = t.history(period="2d")
            if hist_2d.empty:
                return JsonResponse({'error': 'No market data available.'}, status=404)
            last_close = float(hist_2d['Close'].iloc[-1])
            prev_close = float(hist_2d['Close'].iloc[-2]) if len(hist_2d) > 1 else last_close

        change_pct = ((last_close - prev_close) / prev_close * 100.0) if prev_close else 0.0

        # Get 30 days of history for the sparkline
        hist_30d = t.history(period="30d")
        sparkline_data = []
        if not hist_30d.empty:
            sparkline_data = hist_30d['Close'].tolist()

        # Fetch logo from API Ninjas
        logo_url = f"https://via.placeholder.com/32?text={ticker[0]}"  # Default placeholder
        api_key = config('API_NINJAS_KEY', default=None)
        if api_key:
            api_url = f'https://api.api-ninjas.com/v1/logo?name={stock_name}'
            headers = {'X-Api-Key': api_key}
            try:
                response = requests.get(api_url, headers=headers, timeout=5)
                if response.status_code == 200 and response.json():
                    # Assuming the first result is the most relevant
                    logo_data = response.json()
                    if logo_data and logo_data[0].get('image'):
                        logo_url = logo_data[0]['image']
            except requests.exceptions.RequestException as e:
                # Log the error, but don't fail the whole request
                print(f"Could not fetch logo for {stock_name}: {e}")

        return JsonResponse({
            'ticker': ticker.upper(),
            'stock_name': stock_name,
            'price': f"{last_close:.2f}",
            'change_percent': f"{change_pct:.2f}",
            'sparkline': sparkline_data,
            'logo_url': logo_url
        })
    except Exception as e:
        return JsonResponse({'error': f'Failed to fetch stock card data: {e}'}, status=502)


@require_http_methods(["GET"])
def stock_quote_api(request):
    """GET /api/stock/quote?ticker=XXXX"""
    ticker = request.GET.get('ticker')
    if not ticker:
        return JsonResponse({'error': 'Ticker symbol is required.'}, status=400)

    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="2d")
        if hist is None or hist.empty:
            return JsonResponse({'error': 'No market data available.'}, status=404)

        last_close = float(hist['Close'].iloc[-1])
        prev_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else last_close
        change_pct = ((last_close - prev_close) / prev_close * 100.0) if prev_close else 0.0

        return JsonResponse({
            'ticker': ticker.upper(),
            'price': f"{last_close:.2f}",
            'prev_close': f"{prev_close:.2f}",
            'change_percent': f"{change_pct:.2f}"
        })
    except Exception as e:
        return JsonResponse({'error': f'Failed to fetch quote: {e}'}, status=502)


@require_http_methods(["GET"])
def stock_history_api(request, ticker):
    """
    GET /api/stock/<ticker>/history/
    Returns 1 year of historical closing prices for a stock.
    """
    if not ticker:
        return JsonResponse({'error': 'Ticker symbol is required.'}, status=400)

    try:
        t = yf.Ticker(ticker)
        # Get 1 year of daily data
        hist = t.history(period="1y")
        if hist.empty:
            return JsonResponse({'error': 'No historical data available.'}, status=404)

        # Format data for charting libraries
        # Reset index to make 'Date' a column
        hist = hist.reset_index()
        # Ensure Date is in string format
        hist['Date'] = hist['Date'].dt.strftime('%Y-%m-%d')

        # Select only Date and Close columns
        chart_data = hist[['Date', 'Close']].to_dict(orient='records')

        return JsonResponse({'ticker': ticker.upper(), 'history': chart_data})
    except Exception as e:
        return JsonResponse({'error': f'Failed to fetch historical data: {e}'}, status=502)


@login_required
@require_http_methods(["POST"])
def stock_journals_api(request):
    """POST /api/stock/journals
    Creates a stock journal, its trades, and a post from a single request.
    """
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    # Extract fields from payload
    ticker = (payload.get('ticker_symbol') or '').strip().upper()
    legs_data = payload.get('legs')
    visibility = payload.get('visibility', 'private')
    content = (payload.get('content') or '').strip()
    screenshot_url = (payload.get('screenshot_url') or '').strip()
    title = (payload.get('title') or f"{ticker} 매매일지").strip()

    # Validate required fields
    if not ticker or not legs_data or not isinstance(legs_data, list):
        return JsonResponse({'error': 'ticker_symbol and a list of legs are required.'}, status=400)

    try:
        target_price = Decimal(str(payload.get('target_price')))
        stop_price = Decimal(str(payload.get('stop_price')))
    except (TypeError, ValueError, decimal.InvalidOperation):
        return JsonResponse({'error': 'Invalid target_price or stop_price.'}, status=400)

    user = request.user

    with transaction.atomic():
        stock_info, _ = StockInfo.objects.get_or_create(
            ticker_symbol=ticker,
            defaults={'stock_name': ticker}  # Default name, can be updated later
        )

        journal = StockJournal.objects.create(
            user=user,
            ticker_symbol=stock_info,
            target_price=target_price,
            stop_price=stop_price,
        )

        # Create trades from legs
        for leg in legs_data:
            side = (leg.get('side') or '').upper()
            trade_date = parse_date(leg.get('date') or '')
            if not (side in StockTrade.Side.values and trade_date):
                # This will roll back the transaction
                raise ValueError('Invalid leg data: side and date are required.')

            try:
                price_per_share = Decimal(str(leg.get('price_per_share')))
                quantity = Decimal(str(leg.get('quantity')))
                if quantity <= 0:
                    raise ValueError("Quantity must be positive.")
            except Exception as e:
                raise ValueError(f'Invalid price or quantity in leg: {e}')

            # The StockTrade.save() method automatically triggers journal recalculation
            StockTrade.objects.create(
                journal=journal,
                user=user,
                ticker_symbol=stock_info,
                side=side,
                trade_date=trade_date,
                price_per_share=price_per_share,
                quantity=quantity,
                fee_rate=leg.get('fee_rate'),
                tax_rate=leg.get('tax_rate'),
            )

        # Create the associated post
        post = JournalPost.objects.create(
            user=user,
            asset_class=JournalPost.AssetClass.STOCK,
            stock_journal=journal,
            visibility=visibility,
            title=title,
            content=content,
            screenshot_url=screenshot_url,
        )

    # Reload the journal to get the final aggregated values
    journal.refresh_from_db()

    card_html = render_to_string('_card_stock.html', {'post': post})
    return JsonResponse({
        'post_id': post.id,
        'card_html': card_html,
        'journal_status': journal.status,
        'realized_pnl': journal.realized_pnl,
        'net_qty': journal.net_qty,
    }, status=201)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def add_stock_trade_api(request, journal_id):
    """
    POST /api/stock/journals/<journal_id>/trades/
    Adds a trade to an existing stock journal.
    Expects JSON: { side, trade_date, price_per_share, quantity }
    """
    user = request.user
    journal = get_object_or_404(StockJournal, pk=journal_id, user=user)

    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    side = (payload.get('side') or '').upper()
    if side not in StockTrade.Side.values:
        return JsonResponse({'error': f'Invalid trade side. Must be one of {StockTrade.Side.labels}.'}, status=400)

    trade_date = parse_date(payload.get('trade_date') or '')
    if not trade_date:
        return JsonResponse({'error': 'Trade date is required.'}, status=400)

    try:
        price_per_share = Decimal(str(payload.get('price_per_share')))
        quantity = Decimal(str(payload.get('quantity')))
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
    except Exception as e:
        return JsonResponse({'error': f'Invalid price or quantity. {e}'}, status=400)

    trade = StockTrade.objects.create(
        journal=journal,
        user=user,
        ticker_symbol=journal.ticker_symbol,
        side=side,
        trade_date=trade_date,
        price_per_share=price_per_share,
        quantity=quantity,
        # fee/tax can be added later
    )

    # The model's save() method will trigger recalculation.
    # Reload the journal to get the updated values.
    journal.refresh_from_db()

    return JsonResponse({
        'trade_id': trade.id,
        'journal_status': journal.status,
        'realized_pnl': journal.realized_pnl,
        'net_qty': journal.net_qty,
    }, status=201)


@require_http_methods(["GET"])
def realty_suggest_api(request):
    """GET /api/realty/suggest?address=..."""
    address = request.GET.get('address')
    if not address:
        return JsonResponse({'error': 'Address is required.'}, status=400)

    kakao_key = config('KAKAO_REST_KEY', default='')
    if not kakao_key:
        return JsonResponse({'error': 'Kakao REST key not configured.'}, status=500)

    try:
        resp = requests.get(
            'https://dapi.kakao.com/v2/local/search/address.json',
            params={'query': address},
            headers={'Authorization': f'KakaoAK {kakao_key}'},
            timeout=5
        )
        if resp.status_code != 200:
            return JsonResponse({'error': f'Kakao API error {resp.status_code}'}, status=502)
        data = resp.json()
        docs = data.get('documents', [])
        suggestions = []
        for d in docs:
            addr = d.get('address') or d.get('road_address') or {}
            suggestions.append({
                'name': addr.get('address_name') or address,
                'address': addr.get('address_name') or address,
                'lat': d.get('y'),
                'lng': d.get('x'),
                'region_1depth_name': addr.get('region_1depth_name'),
                'region_2depth_name': addr.get('region_2depth_name'),
                'region_3depth_name': addr.get('region_3depth_name'),
            })
        return JsonResponse({'suggestions': suggestions})
    except Exception as e:
        return JsonResponse({'error': f'Kakao request failed: {e}'}, status=502)


@login_required
@require_http_methods(["POST"])
def realty_deals_api(request):
    """POST /api/realty/deals
    Minimal creation without external fetch.
    Expects JSON with property and deal fields.
    """
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    user = request.user

    # Required minimal fields
    building_name = (payload.get('building_name') or '').strip()
    address_base = (payload.get('address_base') or '').strip()
    property_type = (payload.get('property_type') or 'apartment').strip()
    lawd_cd = (payload.get('lawd_cd') or '').strip()[:5]
    dong = (payload.get('dong') or '').strip()
    lat = Decimal(str(payload.get('lat') or '0'))
    lng = Decimal(str(payload.get('lng') or '0'))

    deal_type = (payload.get('deal_type') or '매매').strip()
    contract_date = parse_date(payload.get('contract_date') or '')
    if not (building_name and address_base and contract_date):
        return JsonResponse({'error': 'Missing required fields.'}, status=400)

    try:
        amount_main = Decimal(str(payload.get('amount_main') or '0'))
        amount_deposit = Decimal(str(payload.get('amount_deposit') or '0'))
        amount_monthly = Decimal(str(payload.get('amount_monthly') or '0'))
        area_m2 = Decimal(str(payload.get('area_m2') or '0'))
        floor = int(payload.get('floor') or 0)
    except Exception:
        return JsonResponse({'error': 'Invalid numeric fields.'}, status=400)

    with transaction.atomic():
        prop, created = REPropertyInfo.objects.get_or_create(
            address_base=address_base,
            building_name=building_name,
            defaults={
                'property_type': property_type,
                'lawd_cd': lawd_cd,
                'dong': dong,
                'lat': lat,
                'lng': lng,
            }
        )
        deal = REDeal.objects.create(
            user=user,
            property_info=prop,
            deal_type=deal_type,
            contract_date=contract_date,
            amount_main=amount_main,
            amount_deposit=amount_deposit,
            amount_monthly=amount_monthly,
            area_m2=area_m2,
            floor=floor,
        )
        post = JournalPost.objects.create(
            user=user,
            asset_class=JournalPost.AssetClass.REAL_ESTATE,
            re_deal=deal,
            title=payload.get('title') or f'{building_name} {deal_type} 계약',
            content=payload.get('content') or '',
        )

    card_html = render_to_string('_card_realty.html', {'post': post})
    return JsonResponse({'post_id': post.id, 'card_html': card_html}, status=201)


@login_required
@require_http_methods(["PATCH", "DELETE"])
def journal_post_api(request, post_id):
    """
    PATCH, DELETE /api/journal-posts/<post_id>/
    - PATCH: Updates the content of a journal post.
    - DELETE: Deletes a journal post and its related journal/deal.
    """
    user = request.user
    post = get_object_or_404(JournalPost, pk=post_id, user=user)

    if request.method == 'PATCH':
        try:
            payload = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

        content = payload.get('content')
        if content is None:
            return JsonResponse({'error': 'Content field is required.'}, status=400)

        post.content = str(content).strip()
        post.save(update_fields=['content', 'updated_at'])

        return JsonResponse({'post_id': post.id, 'content': post.content})

    elif request.method == 'DELETE':
        with transaction.atomic():
            # Manually delete the root journal/deal, which will then cascade
            # and delete the post itself, along with any related trades.
            if post.stock_journal:
                post.stock_journal.delete()
            elif post.re_deal:
                post.re_deal.delete()
            else:
                # Fallback in case the post is orphaned, though this shouldn't happen
                # with the CHECK constraint in the model.
                post.delete()
        return JsonResponse({}, status=204)


from django.db.models import Prefetch

def posts_api(request):
    """GET /api/posts?visibility=public"""
    visibility = request.GET.get('visibility', 'public')
    if visibility != 'public':
        return JsonResponse({'posts': []})

    # Eagerly load related objects to prevent N+1 queries to our DB
    posts = JournalPost.objects.filter(
        visibility=JournalPost.Visibility.PUBLIC
    ).select_related(
        'user', 'stock_journal__ticker_symbol', 're_deal__property_info'
    ).order_by('-created_at')[:50]  # Add pagination limit

    # For stock signals, collect all unique tickers for a single batch yfinance request
    stock_journals = [p.stock_journal for p in posts if p.asset_class == 'stock' and p.stock_journal]
    tickers_to_fetch = {journal.ticker_symbol.ticker_symbol for journal in stock_journals}

    current_prices = {}
    if tickers_to_fetch:
        try:
            ticker_data = yf.Tickers(' '.join(tickers_to_fetch))
            for ticker_str, ticker_obj in ticker_data.tickers.items():
                last_price = ticker_obj.fast_info.get('lastPrice')
                if last_price:
                    current_prices[ticker_str] = Decimal(str(last_price))
        except Exception as e:
            print(f"Error fetching batch stock data from yfinance: {e}")

    # Build the final JSON response
    response_posts = []
    for post in posts:
        post_data = {
            'id': post.id,
            'user': {
                'username': post.user.username,
            },
            'asset_class': post.asset_class,
            'title': post.title,
            'content': post.content,
            'created_at': post.created_at.isoformat(),
        }

        if post.asset_class == 'stock' and post.stock_journal:
            journal = post.stock_journal
            ticker = journal.ticker_symbol.ticker_symbol
            current_price = current_prices.get(ticker)
            signal = 'yellow'  # Default signal

            if current_price:
                if journal.target_price and current_price >= journal.target_price:
                    signal = 'green'
                elif journal.stop_price and current_price <= journal.stop_price:
                    signal = 'red'
            
            post_data['asset_details'] = {
                'ticker': ticker,
                'stock_name': journal.ticker_symbol.stock_name,
                'target_price': journal.target_price,
                'stop_price': journal.stop_price,
                'signal': signal,
            }
        elif post.asset_class == 'realestate' and post.re_deal:
            deal = post.re_deal
            post_data['asset_details'] = {
                'building_name': deal.property_info.building_name,
                'deal_type': deal.deal_type,
                'area_m2': deal.area_m2,
                'amount_main': deal.amount_main,
            }
        
        response_posts.append(post_data)

    return JsonResponse({'posts': response_posts})