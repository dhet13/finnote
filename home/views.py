from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import JournalPost, Like, Comment

@login_required
def create_post_view(request):
    """포스트 작성 페이지"""
    return render(request, 'home/create_post.html')

@login_required
def create_simple_post(request):
    """간단한 텍스트 포스트 작성"""
    if request.method == 'POST':
        content = request.POST.get('content')
        
        if content and content.strip():
            post = JournalPost.objects.create(
                user=request.user,
                content=content.strip(),
                asset_class='stock',  # 기본값
                embed_payload_json={}
            )
            messages.success(request, '포스트가 작성되었습니다!')
        
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

@login_required
def create_simple_post(request):
    """간단한 텍스트 포스트 작성"""
    if request.method == 'POST':
        content = request.POST.get('content')
        
        if content and content.strip():
            post = JournalPost.objects.create(
                user=request.user,
                content=content.strip(),
                asset_class='stock',  # 기본값
                embed_payload_json={}
            )
            messages.success(request, '포스트가 작성되었습니다!')
        else:
            messages.error(request, '내용을 입력해주세요.')
        
        return redirect('home:home')
    
    return redirect('home:home')