# finote

주식·부동산 등 다양한 자산을 포트폴리오로 관리하고, 투자 전략과 매매 일지를 함께 기록·토론,공유 할 수 있는 플랫폼

## 설치 및 실행

### 1. 가상환경 생성 및 활성화

```shell
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows
```

### 2. 패키지 설치

```shell
pip install -r requirements.txt
```

### 3. 환경변수 설정

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고, 내부의 키 값을 채워주세요.

```shell
cp .env.example .env
```

### 4. 데이터베이스 마이그레이션

```shell
python manage.py migrate
```

### 5. 개발 서버 실행

```shell
python manage.py runserver
```

## 운영 규칙

- `develop` 브랜치에 머지된 후, 팀원은 `git pull` 후 반드시 `python manage.py migrate`를 실행합니다.
- 새로운 `makemigrations`는 `develop` 브랜치에 직접 커밋하지 않습니다. 피처 브랜치에서 충분히 검토 후 머지합니다.
