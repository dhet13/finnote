# user_profile/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from accounts.forms import ProfileForm

# 프로필 보기 페이지
@login_required
def my_profile(request):
    return redirect('user_profile:profile', my_ID=request.user.my_ID)

def user_profile(request, my_ID):
    user_to_view = get_object_or_404(get_user_model(), my_ID=my_ID)
    
    context = {
        'user_to_view': user_to_view,
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