from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import JournalPost, Like, Comment
import feedparser
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import FinanceDataReader as fdr


def get_finance_news():
    """금융 뉴스 RSS 파싱"""
    try:
        rss_urls = [
            'https://www.hankyung.com/feed/economy',
            'https://www.yna.co.kr/rss/economy.xml',
            'https://kr.investing.com/rss/news_285.rss',
        ]
        
        articles = []
        
        for rss_url in rss_urls:
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries[:3]:
                # 시간 계산
                try:
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_date = datetime(*entry.published_parsed[:6])
                    else:
                        published_date = datetime.now()
                except:
                    published_date = datetime.now()

                time_diff = datetime.now() - published_date
                minutes_ago = int(time_diff.total_seconds() / 60)

                # 하이브리드 이미지 추출
                image_url = None

                # 1. RSS에서 이미지 확인 (연합뉴스)
                if hasattr(entry, 'media_content') and entry.media_content:
                    image_url = entry.media_content[0].get('url')

                # 2. RSS에 이미지가 없으면 웹스크래핑 시도 (한경, 인베스팅)
                elif 'hankyung' in entry.link or 'investing' in entry.link:
                    try:
                        response = requests.get(entry.link, timeout=3, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # og:image 메타태그 찾기
                        og_image = soup.find('meta', property='og:image')
                        if og_image and og_image.get('content'):
                            image_url = og_image.get('content')
                            
                        # og:image가 없으면 첫 번째 img 태그 찾기
                        if not image_url:
                            first_img = soup.find('img', src=True)
                            if first_img and first_img.get('src'):
                                img_src = first_img.get('src')
                                # 상대경로면 절대경로로 변환
                                if img_src.startswith('/'):
                                    from urllib.parse import urljoin
                                    image_url = urljoin(entry.link, img_src)
                                elif img_src.startswith('http'):
                                    image_url = img_src
                                    
                    except Exception as e:
                        print(f"웹스크래핑 실패 ({entry.title[:20]}...): {e}")
                        image_url = None
                # 뉴스 소스 식별
                news_source = 'default'
                if 'hankyung' in entry.link:
                    news_source = 'hankyung'
                elif 'yna.co.kr' in entry.link:
                    news_source = 'yonhap'
                elif 'investing.com' in entry.link:
                    news_source = 'investing'

                articles.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published': published_date,
                    'minutes_ago': minutes_ago,
                    'summary': entry.get('summary', '')[:100] + '...',
                    'image_url': image_url,
                    'news_source': news_source,
                })

        return articles[:9]
        
    except Exception as e:
        print(f"RSS 파싱 오류: {e}")
        return []


@login_required
def create_post_view(request):
    """포스트 작성 페이지"""
    return render(request, 'home/create_post.html')

@login_required
def create_simple_post(request):
    """간단한 텍스트 포스트 작성"""
    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image')
        
        if content and content.strip():
            post = JournalPost.objects.create(
                user=request.user,
                content=content.strip(),
                asset_class='stock',
                embed_payload_json={},
                image=image
            )
            
            # JSON 응답 반환 (AJAX용)
            return JsonResponse({
                'success': True,
                'post': {
                    'username': post.user.username,
                    'content': post.content,
                    'asset_class': post.asset_class,
                    'asset_class_display': post.get_asset_class_display(),
                    'image_url': post.image.url if post.image else None,
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': '내용을 입력해주세요.'
            })
    
    return redirect('home:home')

@login_required
def create_trading_post(request):
    """매매일지 포스트 작성"""
    if request.method == 'POST':
        content = request.POST.get('content')
        trading_symbol = request.POST.get('trading_symbol')
        trading_name = request.POST.get('trading_name')
        trading_side = request.POST.get('trading_side')
        trading_quantity = request.POST.get('trading_quantity')
        trading_price = request.POST.get('trading_price')
        
        # embed_payload_json 생성
        embed_data = {
            'symbol': trading_symbol,
            'name': trading_name,
            'side': trading_side,
            'quantity': trading_quantity,
            'price': trading_price
        }
        
        post = JournalPost.objects.create(
            user=request.user,
            content=content,
            asset_class='stock',
            embed_payload_json=embed_data,
            trading_symbol=trading_symbol,
            trading_name=trading_name,
            trading_side=trading_side,
            trading_quantity=trading_quantity,
            trading_price=trading_price
        )
        
        messages.success(request, '매매일지가 작성되었습니다!')
        return redirect('home:home')
    
    return render(request, 'home/create_trading.html')

@login_required  
def create_image_post(request):
    """이미지 포스트 작성"""
    if request.method == 'POST':
        content = request.POST.get('content')
        # 이미지 처리는 나중에 구현
        
        post = JournalPost.objects.create(
            user=request.user,
            content=content,
            asset_class='stock',  # 임시
            embed_payload_json={}
        )
        
        messages.success(request, '이미지 포스트가 작성되었습니다!')
        return redirect('home:home')
    
    return render(request, 'home/create_image.html')

def home_view(request):
    """홈화면 피드"""
    posts = JournalPost.objects.select_related('user').prefetch_related('likes', 'comments')[:20]
    
    context = {
        'posts': posts,
        'news_articles': get_finance_news(),
        'stock_indices': get_stock_indices('1d'),
        'individual_stocks': get_individual_stocks('1d'),
        'exchange_rates': get_exchange_rates('1d'),
    }
    return render(request, 'home/feed.html', context)

@login_required
def post_detail(request, post_id):
    """포스트 상세보기"""
    post = get_object_or_404(JournalPost, id=post_id)
    comments = post.comments.select_related('user')
    
    context = {
        'post': post,
        'comments': comments,
    }
    return render(request, 'home/post_detail.html', context)

def test_view(request):
    """테스트용 간단한 뷰"""
    posts_count = JournalPost.objects.count()
    users_count = JournalPost.objects.values('user').distinct().count()
    
    return render(request, 'home/test.html', {
        'posts_count': posts_count,
        'users_count': users_count,
    })

def get_stock_indices(period='1d'):
    """주요 지수 데이터 가져오기 (기간별)"""
    try:
        indices = {
            'KOSPI': '^KS11',      # 코스피
            'KOSDAQ': '^KQ11',     # 코스닥  
            'NASDAQ': '^IXIC',     # 나스닥
            'S&P500': '^GSPC'      # S&P 500
        }
        
        # 기간에 따른 데이터 범위 설정 - 항상 비교를 위해 더 많은 데이터 요청
        if period == '1d':
            data_period = '5d'  # 1일 비교를 위해 5일 데이터 요청
        elif period == '5d':
            data_period = '1mo'  # 1주 비교를 위해 1달 데이터 요청
        else:
            data_period = period
        
        index_data = []
        for name, symbol in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=data_period)
                
                if len(hist) >= 1:  # 1개 이상이면 처리
                    current_price = hist['Close'].iloc[-1]
                    
                    # 기간별 비교 기준점 설정
                    if period == '1d':
                        if len(hist) >= 2:
                            prev_price = hist['Close'].iloc[-2]  # 전일 종가
                        else:
                            prev_price = current_price  # 데이터 부족시 변동 없음
                    elif period == '5d':
                        if len(hist) >= 5:
                            prev_price = hist['Close'].iloc[-5]  # 5일 전 종가
                        else:
                            prev_price = hist['Close'].iloc[0]  # 가장 오래된 데이터
                    else:
                        prev_price = hist['Close'].iloc[0]  # 시작점 대비
                    
                    change = current_price - prev_price
                    change_percent = (change / prev_price) * 100 if prev_price != 0 else 0
                    
                    index_data.append({
                        'name': name,
                        'symbol': symbol,
                        'current_price': round(current_price, 2),
                        'change': round(change, 2),
                        'change_percent': round(change_percent, 2),
                        'is_positive': bool(change >= 0),
                        'period': period
                    })
                else:
                    # 데이터가 부족한 경우 기본값
                    index_data.append({
                        'name': name,
                        'symbol': symbol,
                        'current_price': 0,
                        'change': 0,
                        'change_percent': 0,
                        'is_positive': True,
                        'period': period
                    })
            except Exception as e:
                print(f"지수 데이터 오류 ({name}): {e}")
                continue
                
        return index_data
        
    except Exception as e:
        print(f"지수 데이터 전체 오류: {e}")
        return []

def get_individual_stocks(period='1d'):
    """개별 주식 데이터 가져오기 (기간별)"""
    try:
        stocks = [
            {'name': '테슬라', 'symbol': 'TSLA', 'market': 'US'},
            {'name': '엔비디아', 'symbol': 'NVDA', 'market': 'US'},
            {'name': '애플', 'symbol': 'AAPL', 'market': 'US'},
            {'name': '삼성전자', 'symbol': '005930', 'market': 'KR'},
            {'name': 'SK하이닉스', 'symbol': '000660', 'market': 'KR'},
            {'name': '카카오', 'symbol': '035720', 'market': 'KR'},
        ]
        
        stock_data = []
        
        for stock in stocks:
            try:
                if stock['market'] == 'US':
                    # 미국 주식 - yfinance 사용
                    ticker = yf.Ticker(stock['symbol'])
                    hist = ticker.history(period=period)
                    
                    if len(hist) >= 1:  # 1개 이상이면 처리
                        current_price = hist['Close'].iloc[-1]
                        
                        # 기간별 비교 기준점 설정
                        if period == '1d':
                            if len(hist) >= 2:
                                prev_price = hist['Close'].iloc[-2]
                            else:
                                prev_price = current_price
                        elif period == '5d':
                            if len(hist) >= 5:
                                prev_price = hist['Close'].iloc[-5]
                            else:
                                prev_price = hist['Close'].iloc[0]
                        else:
                            prev_price = hist['Close'].iloc[0]
                        
                        change = current_price - prev_price
                        change_percent = (change / prev_price) * 100 if prev_price != 0 else 0
                        
                        stock_data.append({
                            'name': stock['name'],
                            'symbol': stock['symbol'],
                            'market': stock['market'],
                            'current_price': round(current_price, 2),
                            'change': round(change, 2),
                            'change_percent': round(change_percent, 2),
                            'is_positive': bool(change >= 0),
                            'period': period
                        })
                        
                elif stock['market'] == 'KR':
                    # 한국 주식 - finance-datareader 사용
                    from datetime import datetime, timedelta
                    
                    # 기간별 날짜 범위 설정
                    end_date = datetime.now()
                    if period == '1d':
                        start_date = end_date - timedelta(days=7)
                    elif period == '5d':
                        start_date = end_date - timedelta(days=14)
                    elif period == '1mo':
                        start_date = end_date - timedelta(days=60)
                    elif period == '6mo':
                        start_date = end_date - timedelta(days=210)
                    elif period == '1y':
                        start_date = end_date - timedelta(days=400)
                    elif period == '5y':
                        start_date = end_date - timedelta(days=1900)
                    else:
                        start_date = end_date - timedelta(days=30)
                    
                    df = fdr.DataReader(stock['symbol'], start_date, end_date)
                    
                    if len(df) >= 2:
                        current_price = df['Close'].iloc[-1]
                        
                        # 기간별 비교 기준점 설정
                        if period == '1d':
                            prev_price = df['Close'].iloc[-2] if len(df) >= 2 else current_price
                        else:
                            prev_price = df['Close'].iloc[0] if len(df) > 1 else current_price
                        
                        change = current_price - prev_price
                        change_percent = (change / prev_price) * 100 if prev_price != 0 else 0
                        
                        stock_data.append({
                            'name': stock['name'],
                            'symbol': stock['symbol'],
                            'market': stock['market'],
                            'current_price': int(current_price),
                            'change': int(change),
                            'change_percent': round(change_percent, 2),
                            'is_positive': bool(change >= 0),
                            'period': period
                        })
                        
            except Exception as e:
                print(f"주식 데이터 오류 ({stock['name']}): {e}")
                continue
                
        return stock_data
        
    except Exception as e:
        print(f"주식 데이터 전체 오류: {e}")
        return []

def get_exchange_rates(period='1d'):
    """환율 데이터 가져오기 (기간별)"""
    try:
        # 환율은 장기간 데이터 제한
        if period in ['6mo', '1y', '5y', 'max']:
            return []  # 빈 리스트 반환하여 에러 처리
        
        base_url = "https://api.exchangerate-api.com/v4/latest/USD"
        
        try:
            response = requests.get(base_url, timeout=5)
            data = response.json()
            rates = data.get('rates', {})
            
            exchange_pairs = [
                {'name': 'USD/KRW', 'rate_key': 'KRW', 'symbol': 'USD'},
                {'name': 'JPY/KRW', 'rate_key': 'KRW', 'symbol': 'JPY'},  
                {'name': 'EUR/KRW', 'rate_key': 'KRW', 'symbol': 'EUR'},
                {'name': 'CNY/KRW', 'rate_key': 'KRW', 'symbol': 'CNY'},
            ]
            
            exchange_data = []
            krw_rate = rates.get('KRW', 1300)
            
            for pair in exchange_pairs:
                try:
                    if pair['symbol'] == 'USD':
                        current_rate = krw_rate
                    else:
                        other_rate = rates.get(pair['symbol'], 1)
                        current_rate = krw_rate / other_rate
                    
                    # 기간별 변동률 (임시로 랜덤 생성, 실제로는 historical API 필요)
                    import random
                    if period == '1d':
                        change_percent = random.uniform(-2, 2)
                    elif period == '5d':
                        change_percent = random.uniform(-5, 5)
                    else:
                        change_percent = random.uniform(-10, 10)
                    
                    change = current_rate * (change_percent / 100)
                    
                    exchange_data.append({
                        'name': pair['name'],
                        'symbol': pair['symbol'],
                        'current_rate': round(current_rate, 2 if pair['symbol'] == 'JPY' else 0),
                        'change': round(change, 1),
                        'change_percent': round(change_percent, 2),
                        'is_positive': change_percent >= 0,
                        'period': period
                    })
                    
                except Exception as e:
                    print(f"환율 계산 오류 ({pair['name']}): {e}")
                    continue
                    
        except Exception as e:
            print(f"환율 API 오류: {e}")
            return []  # API 실패시 빈 리스트
            
        return exchange_data
        
    except Exception as e:
        print(f"환율 데이터 전체 오류: {e}")
        return []



def get_chart_data(symbol, data_type='stock', period='1d'):
    """차트용 데이터 가져오기 (1일 분봉)"""
    try:
        from datetime import datetime, timedelta
        
        if data_type == 'index':
            # 지수 데이터 (yfinance)
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval="5m" if period == '1d' else "1d")
            
            if len(hist) > 0:
                # 기간별 X축 라벨 포맷 설정
                if period in ['1d', '5d']:
                    labels = [dt.strftime('%H:%M') for dt in hist.index]
                elif period in ['1mo', '6mo']:
                    labels = [dt.strftime('%m/%d') for dt in hist.index]
                else:
                    labels = [dt.strftime('%Y/%m') for dt in hist.index]
                    
                chart_data = {
                    'labels': labels,
                    'data': [round(price, 2) for price in hist['Close'].tolist()],
                    'symbol': symbol
                }
                return chart_data
                
        elif data_type == 'us_stock':
            # 미국 주식 데이터 (yfinance)
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval="5m" if period == '1d' else "1d")
            
            if len(hist) > 0:
                # 기간별 X축 라벨 포맷 설정
                if period in ['1d', '5d']:
                    labels = [dt.strftime('%H:%M') for dt in hist.index]
                elif period in ['1mo', '6mo']:
                    labels = [dt.strftime('%m/%d') for dt in hist.index]
                else:
                    labels = [dt.strftime('%Y/%m') for dt in hist.index]
                    
                chart_data = {
                    'labels': labels,
                    'data': [round(price, 2) for price in hist['Close'].tolist()],
                    'symbol': symbol
                }
                return chart_data
                
        elif data_type == 'kr_stock':
            # 한국 주식 데이터 (finance-datareader) - 일봉으로 대체
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # 1개월 데이터
            
            df = fdr.DataReader(symbol, start_date, end_date)
            
            if len(df) > 0:
                # 최근 20일 데이터만 사용
                df_recent = df.tail(20)
                # 기간별 X축 라벨 포맷 설정
                if period in ['1d', '5d']:
                    labels = [dt.strftime('%m/%d') for dt in df_recent.index]
                elif period in ['1mo', '6mo']:
                    labels = [dt.strftime('%m/%d') for dt in df_recent.index]  
                else:
                    labels = [dt.strftime('%Y/%m') for dt in df_recent.index]

                chart_data = {
                    'labels': labels,
                    'data': [int(price) for price in df_recent['Close'].tolist()],
                    'symbol': symbol
                }
                return chart_data
                
        elif data_type == 'exchange':
            # 환율 그래프용 더미 시계열 (기간별 라벨/데이터 일관성 유지)
            import random
            from datetime import datetime, timedelta

            # 🔁 한글/축약 기간값을 내부 표준으로 정규화 (이 분기에서만 로컬 적용)
            p = (period or '1d').strip()
            if p in ('1주', '1w'):
                p = '5d'
            elif p in ('1달', '1개월'):
                p = '1mo'
            elif p in ('6달', '6개월'):
                p = '6mo'

            # 기준 환율 (간단 샘플)
            base_rate = 1340 if symbol == 'USD' else (9.2 if symbol == 'JPY' else 1450)

            # 기간별 라벨 타임스텝 결정 (모두 '문자열' 라벨로 생성)
            if p == '1d':
                points = 12
                start = datetime.now() - timedelta(hours=points)
                step = timedelta(hours=1)
                labels = [(start + i*step).strftime('%H:%M') for i in range(points)]
            elif p == '5d':
                points = 6  # 5~6개의 일자 포인트
                start = datetime.now() - timedelta(days=5)
                step = timedelta(days=1)
                labels = [(start + i*step).strftime('%m/%d') for i in range(points)]
            elif p == '1mo':
                points = 30
                start = datetime.now() - timedelta(days=30)
                step = timedelta(days=1)
                labels = [(start + i*step).strftime('%m/%d') for i in range(points)]
            elif p == '6mo':
                points = 26
                start = datetime.now() - timedelta(days=180)
                step = timedelta(days=7)
                labels = [(start + i*step).strftime('%m/%d') for i in range(points)]
            elif p == '1y':
                points = 52
                start = datetime.now() - timedelta(days=365)
                step = timedelta(days=7)
                labels = [(start + i*step).strftime('%m/%d') for i in range(points)]
            else:  # '5y' 등
                points = 60
                start = datetime.now() - timedelta(days=5*365)
                step = timedelta(days=30)
                labels = [(start + i*step).strftime('%Y/%m') for i in range(points)]

            # 랜덤 워크 데이터 생성
            cur = base_rate
            data = []
            for _ in range(len(labels)):
                cur *= (1 + random.uniform(-0.004, 0.004))  # ±0.4%
                data.append(round(cur, 2))

            return {
                'labels': labels,  # ✅ 문자열 라벨 (x축 00,00… 방지)
                'data': data,
                'symbol': symbol
            }

            
        return None
        
    except Exception as e:
        print(f"차트 데이터 오류 ({symbol}): {e}")
        return None

def get_stock_chart_data(request):
    """AJAX로 차트 데이터 요청 처리"""
    if request.method == 'GET':
        symbol = request.GET.get('symbol')
        data_type = request.GET.get('type')  # 'index', 'us_stock', 'kr_stock', 'exchange'
        
        period = request.GET.get('period', '1d')
        chart_data = get_chart_data(symbol, data_type, period)
        
        if chart_data:
            return JsonResponse({
                'success': True,
                'chart_data': chart_data
            })
        else:
            return JsonResponse({
                'success': False,
                'error': '차트 데이터를 가져올 수 없습니다.'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})
def get_financial_data(request):
    """AJAX로 기간별 금융 데이터 요청 처리"""
    if request.method == 'GET':
        period = request.GET.get('period', '1d')
        tab = request.GET.get('tab', 'indices')
        
        try:
            if tab == 'indices':
                data = get_stock_indices(period)
            elif tab == 'stocks':
                data = get_individual_stocks(period)
            elif tab == 'exchange':
                data = get_exchange_rates(period)
            else:
                data = []
            
            return JsonResponse({
                'success': True, 
                'data': data,
                'period': period,
                'tab': tab
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})