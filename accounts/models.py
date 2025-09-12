# accounts/models.py

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

# 사용자 관리자(Manager)
class UserManager(BaseUserManager):
    def create_user(self, my_ID, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            my_ID=my_ID,
            email=self.normalize_email(email),
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, my_ID, email, password=None, **extra_fields):
        user = self.create_user(
            my_ID,
            email,
            password,
            **extra_fields
        )
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

# 커스텀 User 모델
class User(AbstractBaseUser):
    my_ID = models.CharField(
        verbose_name='사용자 아이디',
        max_length=50,
        unique=True,
    )
    email = models.EmailField(
        verbose_name='이메일 주소',
        max_length=255,
        unique=True,
    )
    nickname = models.CharField(
        verbose_name='닉네임',
        max_length=50,
    )
    profile_picture = models.ImageField(
        verbose_name='프로필 사진',
        upload_to='profile_pictures/',
        blank=True,
    )
    background_picture = models.ImageField(
        verbose_name='배경 사진',
        upload_to='background_pictures/',
        blank=True,
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_private = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'my_ID'  # 로그인 시 사용할 필드
    REQUIRED_FIELDS = ['email', 'nickname']  # createsuperuser 시 필수 입력 필드

    def __str__(self):
        return self.my_ID

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser