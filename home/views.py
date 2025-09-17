from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Post, Like, Comment, Bookmark, Share, Tag
from django.core.paginator import Paginator
import feedparser
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import FinanceDataReader as fdr
from django.views.decorators.http import require_http_methods
import json
import re
from home.services.trading import (
    build_embed_payload_from_payload,
    create_real_estate_journal_from_embed,
    create_stock_journal_from_embed,
)
from .models import PostReport, HiddenPost



def load_more_posts(request):
    """무한 스크롤용 추가 포스트 로드"""
    page = request.GET.get('page', 1)
    posts_per_page = 10
    
    posts = Post.objects.select_related('user').prefetch_related('likes', 'comments', 'tags').order_by('-created_at')
    paginator = Paginator(posts, posts_per_page)
    
    try:
        posts_page = paginator.page(page)
    except:
        return JsonResponse({'posts': [], 'has_next': False})
    
    posts_data = []
    for post in posts_page:
        # 사용자 좋아요 상태
        is_liked = False
        if request.user.is_authenticated:
            is_liked = Like.objects.filter(user=request.user, journal=post).exists()
        
        posts_data.append({
            'id': post.id,
            'username': post.user.my_ID, 
            'my_ID': post.user.my_ID,
            'content': post.content,
            'image_url': post.image.url if post.image else None,
            'screenshot_url': post.screenshot_url,
            'created_at': post.created_at.strftime('%Y-%m-%d %H:%M'),
            'likes_count': post.likes.count(),
            'comments_count': post.comments.count(),
            'bookmarks_count': post.bookmarks.count(),
            'shares_count': post.shares.count(),
            'is_liked': is_liked,
            'tags': [tag.name for tag in post.tags.all()]
        })
    
    return JsonResponse({
        'posts': posts_data,
        'has_next': posts_page.has_next(),
        'next_page': posts_page.next_page_number() if posts_page.has_next() else None
    })

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
@require_http_methods(["GET", "POST"])
def edit_post(request, post_id):
    """포스트 수정"""
    post = get_object_or_404(Post, id=post_id)
    
    # 작성자 확인
    if post.user != request.user:
        return JsonResponse({'success': False, 'error': '권한이 없습니다.'})
    
    if request.method == 'GET':
        # 수정할 포스트 데이터 반환
        return JsonResponse({
            'success': True,
            'post': {
                'id': post.id,
                'content': post.content,
                'tags': [tag.name for tag in post.tags.all()]
            }
        })
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            content = data.get('content', '').strip()
            
            if not content:
                return JsonResponse({'success': False, 'error': '내용을 입력해주세요.'})
            
            # 해시태그 파싱
            hashtag_pattern = r'#(\w+)'
            hashtags = re.findall(hashtag_pattern, content)
            
            # 본문에서 해시태그 제거
            clean_content = re.sub(hashtag_pattern, '', content).strip()
            clean_content = re.sub(r'\s+', ' ', clean_content)
            
            # 포스트 업데이트
            post.content = clean_content
            post.save()
            
            # 태그 업데이트
            post.tags.clear()
            for tag_name in hashtags:
                tag, created = Tag.objects.get_or_create(
                    name=tag_name,
                    defaults={'is_default': False}
                )
                post.tags.add(tag)
            
            return JsonResponse({
                'success': True,
                'post': {
                    'id': post.id,
                    'content': post.content,
                    'tags': [tag.name for tag in post.tags.all()]
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'})

@login_required
@require_http_methods(["POST"])
def hide_post(request, post_id):
    """포스트 숨기기"""
    post = get_object_or_404(Post, id=post_id)
    
    hidden, created = HiddenPost.objects.get_or_create(
        user=request.user,
        journal=post
    )
    
    return JsonResponse({
        'success': True,
        'hidden': True,
        'message': '포스트를 숨겼습니다.'
    })

@login_required
@require_http_methods(["POST"])
def report_post(request, post_id):
    """포스트 신고"""
    post = get_object_or_404(Post, id=post_id)
    
    try:
        data = json.loads(request.body)
        reason = data.get('reason')
        description = data.get('description', '')
        
        if not reason:
            return JsonResponse({'success': False, 'error': '신고 사유를 선택해주세요.'})
        
        # 이미 신고한 포스트인지 확인
        if PostReport.objects.filter(reporter=request.user, journal=post).exists():
            return JsonResponse({'success': False, 'error': '이미 신고한 포스트입니다.'})
        
        report = PostReport.objects.create(
            reporter=request.user,
            journal=post,
            reason=reason,
            description=description
        )
        
        return JsonResponse({
            'success': True,
            'message': '신고가 접수되었습니다. 검토 후 조치하겠습니다.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'})
@login_required
def create_simple_post(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image')
        
        if content and content.strip():
            # 해시태그 파싱
            hashtag_pattern = r'#(\w+)'
            hashtags = re.findall(hashtag_pattern, content)
            
            # 본문에서 해시태그 제거
            clean_content = re.sub(hashtag_pattern, '', content).strip()
            clean_content = re.sub(r'\s+', ' ', clean_content)  # 중복 공백 제거
            
            normalized_journal_payload = {}
            if trading_journal_data:
                try:
                    normalized_journal_payload = json.loads(trading_journal_data)
                except json.JSONDecodeError as e:
                    print(f"매매일지 데이터 파싱 오류: {e}")
                    normalized_journal_payload = {}

            embed_payload = build_embed_payload_from_payload(normalized_journal_payload)

            post = Post.objects.create(
                user=request.user,
                content=clean_content,
                embed_payload_json=embed_payload or {},
                image=image
            )
<<<<<<< HEAD
            
=======

            if embed_payload:
                try:
                    asset_type = embed_payload.get('asset_type')
                    if asset_type == 'stock':
                        create_stock_journal_from_embed(request.user, post, embed_payload)
                    elif asset_type == 'real_estate':
                        create_real_estate_journal_from_embed(request.user, post, embed_payload)
                    print(f"매매일지 데이터 저장: {embed_payload}")
                except Exception as journal_error:
                    print(f"매매일지 관련 데이터 생성 오류: {journal_error}")
>>>>>>> d8922d3 (전체적인 파일 수정)
            # 태그 처리
            for tag_name in hashtags:
                tag, created = Tag.objects.get_or_create(
                    name=tag_name,
                    defaults={'is_default': False}
                )
                post.tags.add(tag)
            
            return JsonResponse({
                'success': True,
                'post': {
                    'id': post.id,
                    'my_ID': post.user.my_ID,
                    'content': post.content,
                    'image_url': post.image.url if post.image else None,
                    'nickname': post.user.nickname,
                    'tags': [tag.name for tag in post.tags.all()],
<<<<<<< HEAD
                    'username': post.user.my_ID
=======
                    'username': post.user.my_ID,
                    'has_trading_data': bool(embed_payload)
>>>>>>> d8922d3 (전체적인 파일 수정)
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
        content = (request.POST.get('content') or '').strip()
        raw_payload = {
            'asset_type': 'stock',
            'ticker_symbol': request.POST.get('trading_symbol'),
            'company_name': request.POST.get('trading_name'),
            'side': request.POST.get('trading_side'),
            'quantity': request.POST.get('trading_quantity'),
            'price_per_unit': request.POST.get('trading_price'),
            'target_price': request.POST.get('target_price'),
            'stop_price': request.POST.get('stop_price'),
            'trade_reason': request.POST.get('trade_reason'),
            'currency_code': request.POST.get('currency_code'),
            'date': request.POST.get('trade_date'),
            'trade_date': request.POST.get('trade_date'),
        }

        embed_payload = build_embed_payload_from_payload(raw_payload) or {}

        post = Post.objects.create(
            user=request.user,
            content=content,
            embed_payload_json=embed_payload,
        )

        if embed_payload.get('asset_type') == 'stock':
            create_stock_journal_from_embed(request.user, post, embed_payload)

        messages.success(request, '매매일지가 작성되었습니다!')
        return redirect('home:home')

    return render(request, 'home/create_trading.html')

@login_required  
def create_image_post(request):
    """이미지 포스트 작성"""
    if request.method == 'POST':
        content = request.POST.get('content')
        # 이미지 처리는 나중에 구현
        
        post = Post.objects.create(
            user=request.user,
            content=content,
            embed_payload_json={}
        )
        
        messages.success(request, '이미지 포스트가 작성되었습니다!')
        return redirect('home:home')
    
    return render(request, 'home/create_image.html')

@login_required
@require_http_methods(["POST"])
def create_reply(request, comment_id):
    """대댓글 작성"""
    parent_comment = get_object_or_404(Comment, id=comment_id)
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if not content:
            return JsonResponse({'error': '댓글 내용을 입력해주세요.'}, status=400)
        
        reply = Comment.objects.create(
            journal=parent_comment.journal,
            user=request.user,
            parent=parent_comment,
            content=content
        )
        
        return JsonResponse({
            'reply_id': reply.id,
            'my_ID': reply.user.my_ID,
            'nickname': reply.user.nickname,
            'content': reply.content,
            'created_at': reply.created_at.strftime('%Y-%m-%d %H:%M'),
            'comments_count': parent_comment.journal.comments.count()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 요청입니다.'}, status=400)
    
def home_view(request):
    posts = Post.objects.select_related('user').prefetch_related('likes', 'comments', 'tags')[:10]
    
    # 사용자 좋아요 상태 추가
    if request.user.is_authenticated:
        for post in posts:
            post.is_liked_by_user = Like.objects.filter(user=request.user, journal=post).exists()
            post.is_bookmarked_by_user = Bookmark.objects.filter(user=request.user, journal=post).exists()
    else:
        for post in posts:
            post.is_liked_by_user = False
            post.is_bookmarked_by_user = False
            post.is_shared_by_user = False 
    
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
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.select_related('user')
    
    context = {
        'post': post,
        'comments': comments,
    }
    return render(request, 'home/post_detail.html', context)

def test_view(request):
    """테스트용 간단한 뷰"""
    posts_count = Post.objects.count()
    users_count = Post.objects.values('user').distinct().count()
    
    return render(request, 'home/test.html', {
        'posts_count': posts_count,
        'users_count': users_count,
    })
@login_required
@require_http_methods(["POST"])
def delete_post(request, post_id):
    """포스트 삭제"""
    post = get_object_or_404(Post, id=post_id)
    
    # 작성자 확인
    if post.user != request.user:
        return JsonResponse({'success': False, 'error': '권한이 없습니다.'})
    
    post.delete()
    
    return JsonResponse({'success': True})
def get_stock_indices(period='1d'):
    """주요 지수 데이터 가져오기 (기간별) - 에러 처리 강화"""
    try:
        indices = {
            'KOSPI': '^KS11',      
            'KOSDAQ': '^KQ11',     
            'NASDAQ': '^IXIC',     
            'S&P500': '^GSPC'      
        }
        
        # 기간에 따른 데이터 범위 설정
        if period == '1d':
            data_period = '5d'
        elif period == '5d':
            data_period = '1mo'
        else:
            data_period = period
        
        index_data = []
        for name, symbol in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                
                # 한국 지수는 추가 처리
                if symbol in ['^KS11', '^KQ11']:
                    # 더 긴 기간으로 데이터 요청 (휴장일 대비)
                    hist = ticker.history(period='1mo')
                else:
                    hist = ticker.history(period=data_period)
                
                # 데이터 검증 강화
                if len(hist) < 1:
                    print(f"데이터 부족: {name}")
                    continue
                    
                current_price = hist['Close'].iloc[-1]
                
                # 비교 기준점 설정 (더 안전하게)
                if period == '1d':
                    if len(hist) >= 2:
                        prev_price = hist['Close'].iloc[-2]
                    else:
                        # 데이터가 1개밖에 없으면 변동 없음으로 처리
                        prev_price = current_price
                        print(f"Warning: {name} 비교 데이터 부족, 변동 없음으로 처리")
                elif period == '5d':
                    if len(hist) >= 5:
                        prev_price = hist['Close'].iloc[-5]
                    else:
                        prev_price = hist['Close'].iloc[0]
                else:
                    prev_price = hist['Close'].iloc[0]
                
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
                
            except Exception as e:
                print(f"지수 데이터 오류 ({name}): {e}")
                # 오류 발생시 기본값으로 처리 (서비스 중단 방지)
                index_data.append({
                    'name': name,
                    'symbol': symbol,
                    'current_price': 0,
                    'change': 0,
                    'change_percent': 0,
                    'is_positive': True,
                    'period': period,
                    'error': True  # 에러 플래그
                })
                
        return index_data
        
    except Exception as e:
        print(f"지수 데이터 전체 오류: {e}")
        # 전체 오류시 빈 리스트 대신 기본 구조 반환
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
                labels = []
                for dt in hist.index:
                    py_dt = dt.to_pydatetime()
                    if period == '1d':
                        labels.append(py_dt.strftime('%H:%M'))      # 1일: 시간
                    elif period in ['5d', '1mo']:
                        labels.append(py_dt.strftime('%m/%d'))      # 1주/1달: 월/일
                    elif period in ['6mo', '1y']:
                        labels.append(py_dt.strftime('%Y/%m'))      # 6개월/1년: 년/월
                    else:  # 5y
                        labels.append(py_dt.strftime('%Y'))         # 5년: 년도만
                    
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
                labels = []
                for dt in hist.index:
                    py_dt = dt.to_pydatetime()
                    if period == '1d':
                        labels.append(py_dt.strftime('%H:%M'))      # 1일: 시간
                    elif period in ['5d', '1mo']:
                        labels.append(py_dt.strftime('%m/%d'))      # 1주/1달: 월/일
                    elif period in ['6mo', '1y']:
                        labels.append(py_dt.strftime('%Y/%m'))      # 6개월/1년: 년/월
                    else:  # 5y
                        labels.append(py_dt.strftime('%Y'))         # 5년: 년도만
                    
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
                # 기간별 데이터 조정
                if period == '1d':
                    df_recent = df.tail(5)   # 1일이면 5일치만
                else:
                    df_recent = df.tail(20)  # 나머지는 20일치
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

@login_required
@require_http_methods(["POST"])
def toggle_like(request, post_id):
    """좋아요 토글 API"""
    post = get_object_or_404(Post, id=post_id)
    
    like, created = Like.objects.get_or_create(
        journal=post,
        user=request.user
    )
    
    if not created:
        # 이미 좋아요가 있으면 제거
        like.delete()
        liked = False
    else:
        # 새로 좋아요 추가
        liked = True
    
    # 전체 좋아요 수 계산
    likes_count = post.likes.count()
    
    return JsonResponse({
        'liked': liked,
        'likes_count': likes_count
    })
@login_required
@require_http_methods(["POST"])
def toggle_bookmark(request, post_id):
    """북마크 토글 API"""
    post = get_object_or_404(Post, id=post_id)
    
    bookmark, created = Bookmark.objects.get_or_create(
        journal=post,
        user=request.user
    )
    
    if not created:
        # 이미 북마크가 있으면 제거
        bookmark.delete()
        bookmarked = False
    else:
        # 새로 북마크 추가
        bookmarked = True
    
    # 전체 북마크 수 계산
    bookmarks_count = post.bookmarks.count()
    
    return JsonResponse({
        'bookmarked': bookmarked,
        'bookmarks_count': bookmarks_count
    })
@login_required
@require_http_methods(["POST"])
def toggle_share(request, post_id):
    """공유 토글 API"""
    post = get_object_or_404(Post, id=post_id)
    
    share, created = Share.objects.get_or_create(
        journal=post,
        user=request.user
    )
    
    if not created:
        # 이미 공유가 있으면 제거
        share.delete()
        shared = False
    else:
        # 새로 공유 추가
        shared = True
    
    # 전체 공유 수 계산
    shares_count = post.shares.count()
    
    return JsonResponse({
        'shared': shared,
        'shares_count': shares_count
    })
@login_required
@require_http_methods(["POST"])
def create_comment(request, post_id):
    """댓글 작성 API"""
    post = get_object_or_404(Post, id=post_id)
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        parent_id = data.get('parent_id')  # 대댓글용
        
        if not content:
            return JsonResponse({'error': '댓글 내용을 입력해주세요.'}, status=400)
        
        # 부모 댓글 확인 (대댓글인 경우)
        parent = None
        if parent_id:
            parent = get_object_or_404(Comment, id=parent_id, journal=post)
        
        comment = Comment.objects.create(
            journal=post,
            user=request.user,
            parent=parent,
            content=content
        )
        
        return JsonResponse({
            'comment_id': comment.id,
            'my_ID': comment.user.my_ID,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
            'comments_count': post.comments.count()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 요청입니다.'}, status=400)

@require_http_methods(["GET"])
def get_comments(request, post_id):
    """댓글 목록 조회 API"""
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(journal=post, parent=None).select_related('user').order_by('created_at')
    
    comments_data = []
    for comment in comments:
        # 대댓글도 가져오기
        replies = Comment.objects.filter(parent=comment).select_related('user').order_by('created_at')
        replies_data = [
            {
                'id': reply.id,
                'my_ID': reply.user.my_ID,
                'nickname': reply.user.nickname,
                'content': reply.content,
                'is_edited': reply.is_edited,
                'created_at': reply.created_at.strftime('%Y-%m-%d %H:%M')
            }
            for reply in replies
        ]
        
        comments_data.append({
            'id': comment.id,
            'my_ID': comment.user.my_ID,
            'content': comment.content,
            'is_edited': comment.is_edited, 
            'nickname': comment.user.nickname,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
            'replies': replies_data,
            'replies_count': len(replies_data) 
        })
    
    return JsonResponse({'comments': comments_data})
@login_required
@require_http_methods(["POST"])
def edit_comment(request, comment_id):
    """댓글 수정"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # 작성자 확인
    if comment.user != request.user:
        return JsonResponse({'success': False, 'error': '권한이 없습니다.'})
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if not content:
            return JsonResponse({'success': False, 'error': '댓글 내용을 입력해주세요.'})
        
        comment.content = content
        comment.is_edited = True
        comment.save()
        
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'is_edited': True,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'})

@login_required
@require_http_methods(["POST"])
def delete_comment(request, comment_id):
    """댓글 삭제"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # 작성자 확인
    if comment.user != request.user:
        return JsonResponse({'success': False, 'error': '권한이 없습니다.'})
    
    comment.delete()
    
    return JsonResponse({'success': True})




