# accounts/urls.py

from django.urls import path
from . import views
from .views import SignupView, CustomLoginView, CustomLogoutView

urlpatterns = [
    # 여기에 accounts 앱의 URL 경로들을 정의할 것입니다.
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
]