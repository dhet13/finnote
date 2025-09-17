from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import logout
from django.contrib import messages

from .forms import CustomUserCreationForm

# 회원가입 뷰
class SignupView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        messages.success(self.request, "가입이 완료되었습니다.")
        return super().form_valid(form)
    

# 로그인 뷰
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

# 로그아웃 뷰
class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')
