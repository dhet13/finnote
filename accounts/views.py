from django.shortcuts import render

# Create your views here.
# def login(request):
#     return render(request,'accounts/login.html')

# accounts/views.py

from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.views import LoginView, LogoutView

from .forms import CustomUserCreationForm

# 회원가입 뷰
class SignupView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'signup.html'
    success_url = reverse_lazy('login')

# 로그인 뷰
class CustomLoginView(LoginView):
    template_name = 'login.html'

# 로그아웃 뷰
class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')