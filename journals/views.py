from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from django.utils.dateparse import parse_date
from django.db import transaction, models
from django.db.models import Q, Sum, F, DecimalField, ExpressionWrapper, Case, When, Value
from django.db.models.functions import Coalesce
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
        template_name = 'journals/_compose_modal.html'
    else:
        template_name = 'journals/compose_page_clean.html'

    asset_type = request.GET.get('asset', 'stock')
    return render(request, template_name, {'asset_type': asset_type})


@login_required
def my_journal_list(request):
    query = request.GET.get('q', '').strip()

    # Aggregate StockJournal data by ticker_symbol for the current user
    # This will give us one entry per unique stock ticker
    stock_summaries = StockJournal.objects.filter(user=request.user) \
        .values('ticker_symbol__ticker_symbol', 'ticker_symbol__stock_name') \
        .annotate(
            # Sum up quantities and PnL from all journals for this ticker
            total_buy_qty_sum=Coalesce(Sum('total_buy_qty'), Decimal(0)),
            total_sell_qty_sum=Coalesce(Sum('total_sell_qty'), Decimal(0)),
            realized_pnl_sum=Coalesce(Sum('realized_pnl'), Decimal(0)),

            # Calculate total value of buys and sells across all journals for this ticker
            # Need to be careful with avg_buy_price * total_buy_qty as avg_buy_price can be None
            total_buy_value_sum=Coalesce(Sum(ExpressionWrapper(
                F('avg_buy_price') * F('total_buy_qty'),
                output_field=DecimalField()
            ), filter=Q(avg_buy_price__isnull=False)), Decimal(0)),
            total_sell_value_sum=Coalesce(Sum(ExpressionWrapper(
                F('avg_sell_price') * F('total_sell_qty'),
                output_field=DecimalField()
            ), filter=Q(avg_sell_price__isnull=False)), Decimal(0)),
        ) \
        .annotate(
            # Calculate overall average buy/sell prices
            overall_avg_buy_price=Case(
                When(total_buy_qty_sum__gt=0, then=ExpressionWrapper(
                    F('total_buy_value_sum') / F('total_buy_qty_sum'),
                    output_field=DecimalField()
                )),
                default=Value(None, output_field=DecimalField()),
                output_field=DecimalField()
            ),
            overall_avg_sell_price=Case(
                When(total_sell_qty_sum__gt=0, then=ExpressionWrapper(
                    F('total_buy_value_sum') / F('total_sell_qty_sum'),
                    output_field=DecimalField()
                )),
                default=Value(None, output_field=DecimalField()),
                output_field=DecimalField()
            ),
        ) \
        .annotate(
            # Calculate overall return rate
            overall_return_rate=Case(
                When(total_sell_qty_sum__gt=0, overall_avg_buy_price__isnull=False, then=ExpressionWrapper(
                    (F('realized_pnl_sum') / (F('overall_avg_buy_price') * F('total_sell_qty_sum'))) * 100,
                    output_field=DecimalField()
                )),
                default=Value(None, output_field=DecimalField()),
                output_field=DecimalField()
            )
        ) \
        .order_by('ticker_symbol__stock_name') # Order by stock name for consistency

    # Filter stock_summaries if query is present
    if query:
        stock_summaries = stock_summaries.filter(
            Q(ticker_symbol__ticker_symbol__icontains=query) |
            Q(ticker_symbol__stock_name__icontains=query)
        )

    # Fetch REDeal objects for the current user (this part remains largely the same)
    re_deals = REDeal.objects.filter(user=request.user) \
        .select_related('property_info') \
        .order_by('-created_at')

    context = {
        'stock_summaries': stock_summaries, # Changed context variable name
        're_deals': re_deals,
        'query': query,
    }
    return render(request, 'journals/my_journal_list.html', context)

@login_required
def stock_detail_view(request, pk):
    stock_journal = get_object_or_404(StockJournal, pk=pk, user=request.user)

    trades = stock_journal.trades.all().order_by('trade_date')

    trade_rows = []
    for trade in trades:
        quantity = trade.quantity or Decimal('0')
        price = trade.price_per_share or Decimal('0')
        total_amount = quantity * price
        buy_amount = total_amount if trade.side == StockTrade.Side.BUY else None
        sell_amount = total_amount if trade.side == StockTrade.Side.SELL else None
        return_rate = None
        if trade.side == StockTrade.Side.SELL and stock_journal.avg_buy_price:
            avg_buy = stock_journal.avg_buy_price
            if avg_buy and avg_buy != 0:
                return_rate = ((price - avg_buy) / avg_buy) * Decimal('100')

        trade_rows.append({
            'instance': trade,
            'side': trade.side,
            'side_label': '매수' if trade.side == StockTrade.Side.BUY else '매도',
            'trade_date': trade.trade_date,
            'quantity': quantity,
            'buy_amount': buy_amount,
            'sell_amount': sell_amount,
            'total_amount': total_amount,
            'return_rate': return_rate,
            'status': stock_journal.get_status_display(),
        })

    journal_posts = JournalPost.objects.filter(stock_journal=stock_journal).order_by('-created_at')

    context = {
        'stock_journal': stock_journal,
        'trade_rows': trade_rows,
        'journal_posts': journal_posts,
    }
    return render(request, 'journals/stock_detail.html', context)


@login_required
def stock_summary_detail(request, ticker_symbol):
    # Fetch all StockJournal entries for the given ticker and current user
    stock_journals = StockJournal.objects.filter(
        user=request.user,
        ticker_symbol__ticker_symbol=ticker_symbol
    ).select_related('ticker_symbol').prefetch_related(
        Prefetch('posts', queryset=JournalPost.objects.order_by('-created_at'))
    ).order_by('-created_at')

    # If no journals found for this ticker, handle appropriately (e.g., 404 or empty list)
    if not stock_journals.exists():
        # Optionally, raise Http404 or render a specific message
        pass # For now, just pass an empty list to the template

    # Get the stock name for display
    stock_name = ticker_symbol
    if stock_journals.first():
        stock_name = stock_journals.first().ticker_symbol.stock_name

    context = {
        'ticker_symbol': ticker_symbol,
        'stock_name': stock_name,
        'stock_journals': stock_journals, # Individual StockJournal objects
        # You might want to pass the aggregated summary here too if needed
    }
    return render(request, 'journals/stock_summary_detail.html', context) # A new template will be needed


@require_http_methods(["GET"])
def stock_search_api(request):
    """
    GET /api/stock/search/?q=...
    Searches for stocks by ticker or name from the local DB.
    This is optimized for speed and does not fetch real-time data.
    """
    query = request.GET.get('q', '').strip()

    if not query or len(query) < 1:
        return JsonResponse({'results': []})

    # Search in both ticker and name, case-insensitive, from our local database
    stocks = StockInfo.objects.filter(
        Q(ticker_symbol__icontains=query) | Q(stock_name__icontains=query)
    ).values('ticker_symbol', 'stock_name')[:10]  # Limit to 10 results

    # Format the results to match the frontend expectation ('ticker' and 'name')
    results = [
        {'ticker': stock['ticker_symbol'], 'name': stock['stock_name']}
        for stock in stocks
    ]

    return JsonResponse({'results': results})


@require_http_methods(["GET"])
def portfolio_summary_api(request):
    """
    GET /api/stock/portfolio-summary/?ticker=...
    Returns summary data for a user's existing stock journal.
    """
    # 로그인 확인
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    ticker = request.GET.get('ticker', '').strip().upper()
    if not ticker:
        return JsonResponse({'error': 'Ticker is required'}, status=400)

    try:
        # StockInfo가 없으면 먼저 생성
        stock_info, created = StockInfo.objects.get_or_create(
            ticker_symbol=ticker,
            defaults={'stock_name': ticker}
        )
        
        journal = StockJournal.objects.get(
            user=request.user,
            ticker_symbol=stock_info
        )
        # If journal is found, return its data
        data = {
            'net_quantity': float(journal.net_qty) if journal.net_qty else 0,
            'average_buy_price': float(journal.avg_buy_price) if journal.avg_buy_price else None,
            'average_sell_price': float(journal.avg_sell_price) if journal.avg_sell_price else None,
            'realized_pnl': float(journal.realized_pnl) if journal.realized_pnl else None,
            'return_rate': float(journal.return_rate) if journal.return_rate else None,
            'status': journal.status,
        }
        return JsonResponse(data)
    except StockJournal.DoesNotExist:
        # If no journal exists for this user/ticker, return empty/zeroed data
        return JsonResponse({
            'net_quantity': 0,
            'average_buy_price': None,
            'average_sell_price': None,
            'realized_pnl': None,
            'return_rate': None,
            'status': 'new',  # A custom status to indicate no position
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
        prev_close = info.get('previousPrice') # Corrected: 'previousClose' to 'previousPrice'
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

        # Simplified: No logo fetching for now to isolate syntax error
        logo_url = f"https://via.placeholder.com/32?text={ticker[0]}"  # Default placeholder

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
    """
    GET /api/stock/quote?ticker=XXXX"""
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
    """
    Creates a stock journal, its trades, and a post from a single request.
    """
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    # Extract fields from payload
    ticker = (payload.get('ticker_symbol') or '').strip().upper()
    legs_data = payload.get('legs')
    visibility = (payload.get('visibility', 'private') or '').strip()
    content = (payload.get('content') or '').strip()
    screenshot_url = (payload.get('screenshot_url') or '').strip()
    title = (payload.get('title') or f"{ticker} 매매일지").strip()

    # Validate required fields
    if not ticker or not legs_data or not isinstance(legs_data, list):
        return JsonResponse({'error': 'ticker_symbol and a list of legs are required.'}, status=400)

    try:
        target_price = Decimal(str(payload.get('target_price')))
        stop_price = Decimal(str(payload.get('stop_price')))
    except (TypeError, ValueError, models.Decimal.InvalidOperation):
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
            except (TypeError, ValueError, models.Decimal.InvalidOperation) as e:
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

    card_html = render_to_string('journals/_card_stock.html', {'post': post})
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

    trade_date = parse_date(payload.get('date') or '') # Corrected: 'trade_date' to 'date'
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

    # The model's save() method will trigger journal recalculation.
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
    """
    GET /api/realty/suggest?address=..."""
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
    """
    Minimal creation without external fetch.
    Expects JSON with property and deal fields.
    """
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    user = request.user

    # Fields from the simplified form
    # payload에서 각 필드의 값을 가져옵니다. 만약 값이 없으면 빈 문자열('')을 기본값으로 사용하고, strip()으로 양쪽 공백을 제거합니다.
    building_name = (payload.get('building_name') or '').strip()
    address_base = (payload.get('address_base') or '').strip()

    # [수정] 'dong' 값을 address_base 필드에서 추출 시도합니다.
    dong = ''
    for part in address_base.split():
        if part.endswith('동') or part.endswith('읍') or part.endswith('면'):
            dong = part
            break # 첫 번째 일치하는 부분을 찾으면 중단

    # [수정] 만약 주소에서 '동'을 찾지 못했다면(도로명 주소 등), 임시로 '-'를 기본값으로 사용합니다.
    # 이렇게 하면 데이터베이스의 NOT NULL 제약조건을 만족시키면서 모든 주소 유형을 저장할 수 있습니다.
    if not dong:
        dong = '-'

    property_type = (payload.get('property_type') or 'apartment').strip()
    deal_type = (payload.get('deal_type') or '매매').strip()
    contract_date = parse_date(payload.get('contract_date') or '')
    amount_main = Decimal(str(payload.get('amount_main') or '0'))
    area_m2 = Decimal(str(payload.get('area_m2') or '0'))
    floor = int(payload.get('floor') or 0)

    # Basic validation for required fields
    # [수정] 필수 정보 검사에서 'dong'을 제외합니다. 위에서 자동으로 채워주기 때문입니다.
    if not (building_name and address_base and contract_date and amount_main):
        return JsonResponse({'error': '필수 정보를 입력해주세요 (건물명, 주소, 계약일, 주요 금액).'}, status=400)

    # Set optional fields to None if not provided by the simplified form
    # These fields were previously in the form but are now removed
    # They are still in the model, so we need to provide a value (e.g., None or default)
    lawd_cd = None
    # [삭제] dong = None  <- 이 줄을 삭제하고 위에서 payload로부터 값을 받도록 수정했습니다.
    
    # [수정] 위도(lat)와 경도(lng) 값도 payload에서 가져오도록 수정했습니다. 
    # 카카오 API 등을 통해 주소를 선택했을 때 받아온 위도, 경도 값이 있다면 그 값을 사용하고, 없다면 기본값 '0'을 사용합니다.
    lat = Decimal(str(payload.get('lat') or '0'))
    lng = Decimal(str(payload.get('lng') or '0'))
    amount_deposit = Decimal('0')
    amount_monthly = Decimal('0')
    loan_amount = None
    loan_rate = None
    fees_broker = None
    tax_acq = None
    reg_fee = None
    misc_cost = None
    content = '' # Memo field

    try:
        # Numeric fields that are now optional in the form but required by model/logic
        # Ensure they are Decimal or int, even if from payload they might be None
        amount_main = Decimal(str(amount_main))
        area_m2 = Decimal(str(area_m2))
        floor = int(floor)

        # Handle optional numeric fields that are not in the simplified form
        # but are in the model. Ensure they are Decimal or int.
        amount_deposit = Decimal(str(amount_deposit))
        amount_monthly = Decimal(str(amount_monthly))

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
            loan_amount=loan_amount,
            loan_rate=loan_rate,
            fees_broker=fees_broker,
            tax_acq=tax_acq,
            reg_fee=reg_fee,
            misc_cost=misc_cost,
        )
        post = JournalPost.objects.create(
            user=user,
            asset_class=JournalPost.AssetClass.REAL_ESTATE,
            re_deal=deal,
            title=f'{building_name} {deal_type} 계약',
            content=content,
        )

    card_html = render_to_string('journals/_card_realty.html', {'post': post})
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
    """
    GET /api/posts?visibility=public"""
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
                last_price = ticker_obj.fast_info.get('lastPrice') # Corrected: 'info.get' to 'ticker_obj.fast_info.get'
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
                'my_id': post.user.my_ID,
                'nickname': post.user.nickname
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