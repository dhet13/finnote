# Finote

투자 포트폴리오 관리 및 매매일지 공유 플랫폼입니다. 주식, 부동산 등 다양한 자산을 체계적으로 관리하고, 투자 전략과 매매 일지를 기록하여 다른 투자자들과 공유하고 토론할 수 있습니다.


## 사이트 주소
https://finnote-8ozn.onrender.com/


## 주요 기능

- 📊 **포트폴리오 관리**: 주식, 부동산 등 다양한 자산 포트폴리오 관리
- 📝 **매매일지**: 투자 기록 및 전략 작성
- 👥 **커뮤니티**: 투자 정보 공유 및 토론
- 📈 **대시보드**: 실시간 자산 현황 및 성과 분석
- 🔐 **사용자 관리**: 프로필 및 계정 관리

## 기획서 및 DB설계

**개발 방식 정의 및 DB설게**  
https://docs.google.com/spreadsheets/d/13FqeeXjzW6RZpImLNQQsNSNjfXjApLTLjHvIFvt5gvQ/edit?gid=1277123083#gid=1277123083

**기획서**
https://www.figma.com/design/E6wMvTz5ItLLMSOKEdY6Ci/%ED%95%80%ED%85%8C%ED%81%AC%EC%95%B1?t=MXYaLRfPn1zPiugN-1


## 소개 / 실행 영상 주소
https://www.youtube.com/watch?v=7rRL2OOv2YM

## 팀 작업일지

👤 김미숙
- **담당 영역**: 매매일지 탭
- **작업 내용**: 매매일지 탭 관련 기능 개발 및 UI 구현
- **발표 준비 내용**: 소개 영상 작업

👤 장혁준
- **담당 영역**: 메인 홈화면
- **작업 내용**: 메인 홈화면 디자인 및 기능 구현
- **발표 준비 내용**: 발표 PPT 제작

👤 백지훈
- **담당 영역**: 회원가입 및 프로필
- **작업 내용**: 사용자 인증 시스템 및 프로필 관리 기능 개발
- **발표 준비 내용**: 사이트 배포

👤 이동혁
- **담당 영역**: 대시보드 앱
- **작업 내용**: 대시보드 관련 기능 및 데이터 시각화 구현
- **발표 준비 내용**: 발표

## 기술 스택

- **Backend**: Django 5.2.6
- **Database**: SQLite (개발용)
- **Frontend**: HTML, CSS, JavaScript
- **외부 API**: Yahoo Finance (yfinance), FinanceDataReader


## 프로젝트 구조

```
finote/
├── accounts/        # 사용자 계정 관리
├── dashboard/       # 대시보드 기능
├── home/           # 홈페이지
├── journals/       # 매매일지 관리
├── finote/         # 메인 앱
├── config/         # Django 설정
├── templates/      # HTML 템플릿
├── static/         # 정적 파일
└── media/          # 업로드된 미디어 파일
```

## 설치 및 실행

### 사전 요구사항
- Python 3.8+
- pip

### 1. 저장소 클론

```bash
git clone <repository-url>
cd clean-finote
```

### 2. 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정

`.env.example` 파일을 참고하여 `.env` 파일을 생성하고 필요한 환경변수를 설정하세요.

```bash
# Windows
copy .env.example .env
# macOS/Linux
cp .env.example .env
```

### 5. 데이터베이스 초기화

```bash
python manage.py migrate
```

### 6. 슈퍼유저 생성 (선택사항)

```bash
python manage.py createsuperuser
```

### 7. 개발 서버 실행

```bash
python manage.py runserver
```

서버가 시작되면 `http://127.0.0.1:8000`에서 애플리케이션에 접근할 수 있습니다.

## 개발 워크플로우

### 브랜치 전략
- `main`: 프로덕션 브랜치
- `develop`: 개발 메인 브랜치
- `feature/*`: 기능 개발 브랜치

### 개발 규칙
1. `develop` 브랜치에서 새로운 기능 브랜치 생성
2. 기능 개발 완료 후 `develop` 브랜치로 Pull Request
3. 코드 리뷰 후 머지
4. `develop` 브랜치 업데이트 후 반드시 `python manage.py migrate` 실행

### 마이그레이션 규칙
- 새로운 `makemigrations`는 `develop` 브랜치에 직접 커밋하지 않음
- 피처 브랜치에서 충분히 검토 후 머지
- 팀원은 `git pull` 후 반드시 `python manage.py migrate` 실행

## 유틸리티 스크립트

프로젝트에는 다음과 같은 유틸리티 스크립트들이 포함되어 있습니다:

- `check_session.py`: 세션 상태 확인
- `check_stock_data.py`: 주식 데이터 확인
- `sync_asset_logs_to_portfolio.py`: 자산 로그 동기화
- `update_portfolio_holdings.py`: 포트폴리오 보유 자산 업데이트

## 라이선스

이 프로젝트는 [라이선스 정보]에 따라 라이선스가 부여됩니다.

## 기여하기

1. 이 저장소를 포크합니다
2. 새로운 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다

## 문의

프로젝트 관련 문의사항이 있으시면 [연락처 정보]로 연락해 주세요.
