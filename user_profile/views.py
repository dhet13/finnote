# user_profile/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from accounts.forms import ProfileForm
from .forms import StockAssetCreateForm, RealEstateAssetForm
from journals.models import StockInfo, StockJournal, StockTrade, REDeal, REPropertyInfo
from decimal import Decimal
from django.http import JsonResponse
import json
from home.models import JournalPost, Like, Bookmark

# 프로필 보기 페이지
@login_required
def my_profile(request):
    return redirect('user_profile:profile', my_ID=request.user.my_ID)

def user_profile(request, my_ID):
    user_to_view = get_object_or_404(get_user_model(), my_ID=my_ID)
    stock_journals = None
    re_deals = None

    if request.user == user_to_view or not user_to_view.is_private:
        stock_journals = StockJournal.objects.filter(user=user_to_view)
        re_deals = REDeal.objects.filter(user=user_to_view)
    
    context = {
        'user_to_view': user_to_view,
        'stock_journals': stock_journals,
        're_deals': re_deals,
        'is_profile_owner': request.user == user_to_view,
    }
    return render(request, 'user_profile/user_profile.html', context)

# 프로필 수정 페이지
@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('user_profile:profile', my_ID=request.user.my_ID)
    else:
        form = ProfileForm(instance=request.user)
    
    context = {'form': form}
    return render(request, 'user_profile/edit_profile.html', context)

# 주식 자산 추가 페이지
@login_required
def add_stock_asset(request):
    if request.method == 'POST':
        form = StockAssetCreateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            # API 등을 통해 얻은 정확한 주식 이름으로 defaults를 채우는 것이 좋습니다.
            # 지금은 ticker_symbol로 임시 저장합니다.
            stock_info, _ = StockInfo.objects.get_or_create(
                ticker_symbol=data['ticker_symbol'],
                defaults={'stock_name': data['ticker_symbol']}
            )
            
            stock_journal, _ = StockJournal.objects.get_or_create(
                user=request.user,
                ticker_symbol=stock_info,
                defaults={
                    'target_price': 0, 
                    'stop_price': 0
                }
            )

            StockTrade.objects.create(
                journal=stock_journal,
                user=request.user,
                ticker_symbol=stock_info,
                side='BUY',
                trade_date=data['trade_date'],
                price_per_share=data['price_per_share'],
                quantity=data['quantity']
            )
            return redirect('user_profile:profile', my_ID=request.user.my_ID)
    else:
        form = StockAssetCreateForm()
    
    context = {'form': form}
    return render(request, 'user_profile/add_stock_asset.html', context)



# 자산 삭제 버튼
@login_required
def delete_stock_asset(request, my_ID, ticker_symbol):
    if request.method == 'POST':
        user = get_object_or_404(get_user_model(), my_ID=my_ID)
        
        # 로그인한 사용자가 프로필 소유자인지 확인
        if request.user.my_ID != user.my_ID:
            return JsonResponse({'success': False, 'message': '권한이 없습니다.'}, status=403)
            
        try:
            stock_journal = get_object_or_404(StockJournal, user=user, ticker_symbol__ticker_symbol=ticker_symbol)
            
            # StockJournal 객체를 삭제하면 관련된 StockTrade 레코드는 자동으로 삭제됩니다.
            stock_journal.delete()
            
            return JsonResponse({'success': True, 'message': '자산이 성공적으로 삭제되었습니다.'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'자산 삭제 중 오류가 발생했습니다: {str(e)}'})

    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'}, status=405)

# 부동산 자산 추가 페이지
@login_required
def add_real_estate_asset(request):
    if request.method == 'POST':
        form = RealEstateAssetForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            # REPropertyInfo 객체 생성 또는 가져오기
            # 사용자가 모든 정보를 직접 입력하므로, 매번 새로운 REPropertyInfo를 생성하거나
            # 주소와 건물 이름으로 기존 정보를 찾아볼 수 있습니다.
            # 여기서는 간단하게 새로 생성하는 것으로 가정합니다.
            property_info = REPropertyInfo.objects.create(
                property_type=data['property_type'],
                building_name=data['building_name'],
                address_base=data['address_base'],
                lawd_cd="00000",  # 임시 값
                dong="",  # 임시 값
                lat=Decimal('0.0'),  # 임시 값
                lng=Decimal('0.0')  # 임시 값
            )
            
            # REDeal 객체 생성
            REDeal.objects.create(
                user=request.user,
                property_info=property_info,
                deal_type=data['deal_type'],
                contract_date=data['contract_date'],
                amount_main=data['amount_main'],
                area_m2=data['area_m2'],
                floor=data['floor']
            )
            
            return redirect('user_profile:profile', my_ID=request.user.my_ID)
    else:
        form = RealEstateAssetForm()
    
    context = {'form': form}
    return render(request, 'user_profile/add_real_estate_asset.html', context)

# 부동산 삭제
@login_required
def delete_real_estate_asset(request, deal_id):
    if request.method == 'POST':
        deal = get_object_or_404(REDeal, id=deal_id)
        
        # 로그인한 사용자가 프로필 소유자인지 확인
        if request.user != deal.user:
            return JsonResponse({'success': False, 'message': '권한이 없습니다.'}, status=403)
            
        try:
            # REDeal 객체를 삭제합니다.
            deal.delete()
            
            return JsonResponse({'success': True, 'message': '자산이 성공적으로 삭제되었습니다.'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'자산 삭제 중 오류가 발생했습니다: {str(e)}'})

    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'}, status=405)

def user_likes_view(request):
              # 현재 사용자가 '좋아요'한 항목을 가져오는 로직
              # 예시:
              # liked_items = LikedItem.objects.filter(user=request.user)
            #   context = {
            #       # 'liked_items': liked_items,
            #   }
              return render(request, 'user_profile/user_likes.html')

@login_required
def my_posts_view(request):
    """
    사용자가 작성한 게시물 목록 뷰
    """
    user = request.user
    my_posts = JournalPost.objects.filter(user=user).order_by('-created_at')
    
    context = {
        'posts': my_posts,
        'title': '내가 작성한 게시물',
        'user_to_view': user
    }
    return render(request, 'user_profile/my_posts.html', context)

@login_required
def liked_posts_view(request):
    """
    사용자가 좋아요를 누른 게시물 목록 뷰
    """
    user = request.user
    liked_posts_ids = Like.objects.filter(user=user).values_list('journal_id', flat=True)
    liked_posts = JournalPost.objects.filter(id__in=liked_posts_ids).order_by('-created_at')
    
    context = {
        'posts': liked_posts,
        'title': '좋아요 누른 게시물',
        'user_to_view': user
    }
    return render(request, 'user_profile/liked_posts.html', context)

@login_required
def bookmarked_posts_view(request):
    """
    사용자가 북마크한 게시물 목록 뷰
    """
    user = request.user
    bookmarked_posts_ids = Bookmark.objects.filter(user=user).values_list('journal_id', flat=True)
    bookmarked_posts = JournalPost.objects.filter(id__in=bookmarked_posts_ids).order_by('-created_at')
    
    context = {
        'posts': bookmarked_posts,
        'title': '북마크한 게시물',
        'user_to_view': user
    }
    return render(request, 'user_profile/bookmarked_posts.html', context)