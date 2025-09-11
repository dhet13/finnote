# user_profile/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from accounts.forms import ProfileForm
from .forms import StockAssetCreateForm
from journals.models import StockInfo, StockJournal, StockTrade
from decimal import Decimal

# 프로필 보기 페이지
@login_required
def my_profile(request):
    return redirect('user_profile:profile', my_ID=request.user.my_ID)

def user_profile(request, my_ID):
    user_to_view = get_object_or_404(get_user_model(), my_ID=my_ID)
    stock_journals = StockJournal.objects.filter(user=user_to_view)
    
    context = {
        'user_to_view': user_to_view,
        'stock_journals': stock_journals,
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

# 자산 추가 페이지
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

def user_likes_view(request):
              # 현재 사용자가 '좋아요'한 항목을 가져오는 로직
              # 예시:
              # liked_items = LikedItem.objects.filter(user=request.user)
            #   context = {
            #       # 'liked_items': liked_items,
            #   }
              return render(request, 'user_profile/user_likes.html')