# user_profile/forms.py

from django import forms
from accounts.models import User # accounts 앱의 User 모델을 임포트

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['nickname','profile_picture', 'background_picture']