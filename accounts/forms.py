# accounts/forms.py

from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('my_ID', 'email', 'nickname') 

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        # 사용자가 수정할 필드만 명시적으로 나열
        fields = ['nickname', 'profile_picture', 'background_picture','is_private']
        # is_private : 공개/비공개 상태
        widgets = {
            'nickname': forms.TextInput(attrs={'class': 'form-control'}),
        }