#!/usr/bin/env python
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def check_sessions():
    print("=== 활성 세션 확인 ===")
    
    # 활성 세션들 확인
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    print(f"활성 세션 수: {active_sessions.count()}")
    
    for session in active_sessions:
        session_data = session.get_decoded()
        print(f"세션 키: {session.session_key}")
        print(f"세션 데이터: {session_data}")
        
        # 사용자 ID가 있는지 확인
        if '_auth_user_id' in session_data:
            user_id = session_data['_auth_user_id']
            try:
                user = User.objects.get(id=user_id)
                print(f"  → 사용자: {user.my_ID} (ID: {user_id})")
            except User.DoesNotExist:
                print(f"  → 사용자 ID {user_id}에 해당하는 사용자가 없습니다.")
        print("---")

if __name__ == '__main__':
    check_sessions()
