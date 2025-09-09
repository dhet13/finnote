당신은 Django 백엔드 + (템플릿 기반) 프런트 구현 도우미입니다.
아래 요구사항을 100% 반영한 실행 가능한 코드를 한 번에 출력하세요.
첨부 엑셀[Team2 핀테크 앱 개발.xlsx]의 내용과 충돌하면, 충돌 항목을 정리한 뒤 내 확인을 기다리세요.

# 반드시 이 형식으로 출력해 주세요
- 모든 코드를 **파일 단위**로 출력합니다.
- 형식(아래 텍스트 그대로 사용):

### FILE: <상대경로/파일명>
<코드>

- 예시:

### FILE: templates/base.html
<!-- 코드 -->

### FILE: apps/journals/urls.py
# 코드


■ 프로젝트/스택
- 프로젝트명: finote
- Python 3.12, Django 5.2.6(LTS), dev DB=SQLite
- 패키지: Pillow 11.3.0, requests 2.32.5, python-decouple 3.8, yfinance
- 보안/운영 규칙:
  · .env.example 커밋, 실제 비밀은 로컬 .env 또는 Secret Manager
  · SECRET_KEY_FALLBACKS 구성
  · develop 머지 후 팀원은 git pull → migrate만(새 makemigrations 금지)
  · 앱별 env prefix는 settings/base.py 한 곳에 정의

■ 웹 공통 레이아웃(피그마/엑셀 규칙)
- Header 고정 높이 60px, 전체 폭 100%, 메인 컨테이너 최대폭 1200px(center)
- Header 좌측 275px: “Home”(20px bold, 좌여백 20px)
- Header 중앙 600px: 검색창(폭≈400px, 높이 40px, radius 20px, placeholder “Search Twitter”)
- Header 우측 325px: 설정 아이콘 24×24, 우여백 20px
- 중앙 피드 컬럼 폭은 항상 ≤ 600px.
- tokens.css(디자인 토큰)만 사용. 색/간격/라운드/그림자는 CSS 변수로(하드코딩 금지).

■ 레이아웃/모달 소유권(중요)
- 공통 템플릿(base.html)에는 3열 그리드와 블록만 제공:
  · {% block left %}{% endblock %} (좌 275), {% block feed %}{% endblock %} (중앙 ≤600), {% block right %}{% endblock %} (우 325)
  · 공통 모달 컨테이너: `<div id="modal-root" hidden></div>`
- 홈(Home)은 **“열기 트리거”만** 담당:
  · “What’s happening?” 달력 아이콘 클릭 시 `openModal('/journals/compose/?asset=stock&modal=1')`
  · 모바일(<768px)에서는 모달 대신 **페이지 이동**: `/journals/compose/?asset=stock`
- **모달 내용/검증/저장은 “매매일지 앱(journals)” 소유**.
- 공통 JS:
  · `openModal(url)` = url GET → partial HTML → `#modal-root` 주입/표시
  · `closeModal()` = 모달 닫기(ESC/배경클릭 포함)
  · 폼 제출(fetch POST) 성공 시 모달 닫고, 응답 `card_html`을 중앙 피드 맨 위에 삽입

■ 데이터 모델(채권 제외)
- stock_info(ticker_symbol PK, stock_name, sector, exchange, currency, last_close_price, updated_at)
- stock_journals: 주식 저널 “표지”
  (id PK, user FK, ticker_symbol FK→stock_info,
   target_price numeric(18,4), stop_price numeric(18,4),
   total_buy_qty numeric(18,6) default 0, total_sell_qty numeric(18,6) default 0,
   avg_buy_price numeric(18,4) nullable, avg_sell_price numeric(18,4) nullable,
   net_qty numeric(18,6) default 0, realized_pnl numeric(18,2) nullable,
   status enum('open','completed') default 'open',
   created_at, updated_at)
- stock_trades: 주식 거래 “줄(leg)”
  (id PK, journal FK→stock_journals, user FK, ticker_symbol FK→stock_info,
   side enum('BUY','SELL'), trade_date date,
   price_per_share numeric(18,4), quantity numeric(18,6),
   fee_rate numeric(6,2) null, tax_rate numeric(6,2) null,
   fee_amount numeric(18,2) null, tax_amount numeric(18,2) null,
   created_at, updated_at)
- re_property_info(property_info_id PK, property_type, building_name, address_base, lawd_cd char(5), dong, build_year int,
                   lat numeric(10,7), lng numeric(10,7), total_floor int, total_units int, exclusive_types json, updated_at)
- re_deals(id PK, user FK, property_info FK, deal_type enum('매수','매도','전세','월세'),
          contract_date date, amount_main numeric(18,0),
          amount_deposit numeric(18,0), amount_monthly numeric(18,0),
          area_m2 numeric(8,2), floor int,
          loan_amount numeric(18,0) null, loan_rate numeric(6,2) null,
          fees_broker numeric(18,0) null, tax_acq numeric(18,0) null, reg_fee numeric(18,0) null, misc_cost numeric(18,0) null,
          raw_snapshot_json json, snapshot_source varchar(20), snapshot_fetched_at timestamptz,
          created_at, updated_at)
- journal_posts(id PK, user FK, visibility enum('public','private'), asset_class enum('stock','realestate'),
               stock_journal_id FK null, re_deal_id FK null, title, content, screenshot_url, created_at, updated_at)

■ REST API
- GET /api/stock/quote?ticker=XXXX
  · yfinance로 현재가/전일증감(%) 스냅샷. 실패 시 최근 60초 캐시 리턴.
- GET /journals/compose/  ← 페이지/모달 공용
  · `modal=1` → 모달 partial HTML(`_compose_modal.html`)
  · 없으면 전체 페이지(`compose_page.html`), `asset=stock|realestate` 초기 탭 선택
- POST /api/stock/journals
  · body 예:
    {
      "ticker_symbol":"005930.KS",
      "legs":[
        {"side":"BUY","date":"2025-09-01","price_per_share":70000,"quantity":10},
        {"side":"BUY","date":"2025-09-03","price_per_share":69000,"quantity":5},
        {"side":"SELL","date":"2025-09-10","price_per_share":72000,"quantity":8}
      ],
      "target_price":75000, "stop_price":66000,
      "visibility":"public", "content":"왜 샀는지", "screenshot_url":"/media/..."
    }
  · 저장 집계:
    avg_buy_price = (Σ(BUY price*qty + BUY 수수료·세금) / Σ(BUY qty))
    avg_sell_price = (Σ(SELL price*qty - SELL 수수료·세금) / Σ(SELL qty))
    net_qty = total_buy_qty - total_sell_qty
    realized_pnl = Σ(SELL price*qty - 수수료·세금) - (avg_buy_price * total_sell_qty)
    status = (net_qty==0 ? "completed" : "open")
  · response: { post_id, net_qty, avg_buy_price, realized_pnl, status, card_html }
- GET /api/realty/suggest?address=...&prop=아파트&months=6
  · 카카오 지오코딩→법정동코드(앞5자리)→국토부 실거래(YYYYMM) 합쳐 최근 1~3건 정규화.
- POST /api/realty/deals
  · re_property_info 찾거나 생성 → re_deals 저장(raw_snapshot_json 포함) → journal_posts 생성
  · response: { post_id, card_html }
- GET /api/posts?visibility=public
  · 주식 카드에 signal 추가: green(현재가≥목표), red(현재가≤손절), yellow(그 외)

■ 프런트(템플릿/접근성)
- Header 60px / Container 1200px / 중앙 피드 ≤600px, tokens.css만 사용.
- “매매 일지 작성”:
  · 홈 달력 → `openModal('/journals/compose/?asset=stock&modal=1')`
  · 모바일(<768px): `/journals/compose/?asset=stock`로 페이지 이동
- 모달(매매일지 앱 소유):
  · 탭: 주식/부동산
  · 주식: 종목 검색 → 현재가 표시 → 거래줄 추가/삭제 → 자동 요약(평단/순수량/손익/상태) → 목표/손절 → 공개/코멘트 → html2canvas 캡처(실패 시에도 저장 가능)
  · 부동산: 주소 입력 → 자동채움 → 유형/단지/면적/층/계약일/금액 → 공개/코멘트 → 캡처(실패 허용)
- 성공 시: 응답 `card_html`을 피드 맨 위에 삽입
- 접근성: 모달 포커스트랩, ESC 닫기, 닫힘 후 포커스 복귀

■ 보안/운영/테스트
- .env.example 제공(SECRET_KEY, KAKAO_REST_KEY, MOLIT_SERVICE_KEY, YF_SOURCE 등)
- CORS/CSRF 안전 기본값, 간단한 Rate limit
- 단위테스트:
  · 집계 로직(평단/손익/상태)
  · 부동산 실거래 정규화
  · `/journals/compose/?modal=1`는 partial, 쿼리 없음은 페이지 렌더
- README: 설치/실행, 환경변수, 마이그레이션/운영 규칙 명시

■ Django 구현 규칙(중요)
- enum은 **CharField(choices=…)** 로 구현(장고에 enum 타입 없음)
- `timestamptz` → **DateTimeField(timezone aware)** (`USE_TZ=True`)
- 유저 FK는 **settings.AUTH_USER_MODEL** 사용
- JSON → **models.JSONField(default=dict or list)**
- Decimal 계산은 `Decimal`로 합산/반올림(quantize)로 정밀도 보장

■ 무결성/인덱스
- `journal_posts` 체크:
  - asset_class='stock' ⇒ stock_journal_id NOT NULL AND re_deal_id IS NULL
  - asset_class='realestate' ⇒ re_deal_id NOT NULL AND stock_journal_id IS NULL
- 인덱스:
  - stock_journals(user, ticker_symbol), stock_trades(journal, trade_date)
  - re_deals(user, property_info, contract_date), journal_posts(user, visibility, created_at)

■ 응답/상태 코드
- 생성 성공: **HTTP 201 + { post_id, card_html, … }**
- 검증 실패: **HTTP 400**, 인증 문제: **HTTP 401/403**

■ 최소 파일(누락 금지)
- `templates/base.html`, `templates/home.html`
- `templates/journals/_compose_modal.html`, `templates/journals/compose_page.html`
- `templates/journals/_card_stock.html`, `templates/journals/_card_realty.html`
- `static/js/modal.js`, `static/tokens.css` (+ html2canvas CDN include)
- `apps/journals/urls.py`, `apps/journals/views.py`, `apps/journals/models.py`, `apps/journals/tests.py`
- `.env.example`, `.gitignore`, `README.md`

# 마지막 지시(핵심 요약)
- 홈은 **달력 아이콘 → openModal()** 트리거만.
- 모달 **내용/검증/저장 = journals 앱 소유**.
- 저장 성공 응답의 **`card_html`을 중앙 피드(≤600px) 맨 위**에 삽입.
