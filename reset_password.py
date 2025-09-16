#!/usr/bin/env python
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User

def reset_password():
    print("=== 비밀번호 재설정 ===")
    
    try:
        # 1번 유저 찾기
        user = User.objects.get(id=1)
        print(f"사용자: {user.my_ID}")
        print(f"이메일: {user.email}")
        
        # 비밀번호를 test123으로 재설정
        user.set_password('test123')
        user.save()
        
        print("✅ 비밀번호가 'test123'으로 재설정되었습니다.")
        
        # 로그인 테스트
        from django.contrib.auth import authenticate
        auth_user = authenticate(my_ID='Fortest-home', password='test123')
        if auth_user:
            print("✅ 로그인 테스트 성공!")
        else:
            print("❌ 로그인 테스트 실패")
            
    except User.DoesNotExist:
        print("❌ 1번 유저를 찾을 수 없습니다.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == '__main__':
    reset_password()