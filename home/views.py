from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import JournalPost, Like, Comment
import feedparser
from datetime import datetime
import requests
from bs4 import BeautifulSoup



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
