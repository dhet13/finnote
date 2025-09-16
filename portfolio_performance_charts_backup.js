// 포트폴리오 수익률 차트 관련 함수들

// Chart.js DataLabels 플러그인 등록
if (typeof Chart !== 'undefined' && Chart.register && typeof ChartDataLabels !== 'undefined') {
    Chart.register(ChartDataLabels);
}

// 로그인 상태 확인 및 포트폴리오 페이지 초기화
async function initializePortfolioPageWithAuth() {
    try {
        // 로그인 상태 확인
        const response = await fetch('/dashboard/api/total/?interval=weekly', {
            credentials: 'same-origin'
        });
        
        if (response.status === 401) {
            console.log('포트폴리오 페이지: 로그인되지 않은 사용자입니다. 로그인 안내를 표시합니다.');
            showPortfolioLoginRequired();
            return false; // 로그인되지 않음
        }
        
        // 로그인된 경우 포트폴리오 초기화
        initializePortfolioPage();
        return true; // 로그인됨
        
    } catch (error) {
        console.error('포트폴리오 페이지 로그인 상태 확인 중 오류:', error);
        showPortfolioLoginRequired();
        return false; // 오류 발생
    }
}

// 포트폴리오 페이지 로그인 안내 표시
function showPortfolioLoginRequired() {
    // 포트폴리오 메인 콘텐츠를 로그인 안내로 교체
    const portfolioMainContent = document.querySelector('.portfolio-main-content');
    if (portfolioMainContent) {
        portfolioMainContent.innerHTML = `
            <div style="
                background: #f7f9fa;
                padding: 60px 20px;
                border-radius: 8px;
                text-align: center;
                margin: 20px 0;
                min-height: 400px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            ">
                <div style="font-size: 28px; color: #0f1419; margin-bottom: 16px; font-weight: 600;">
                    📊 포트폴리오 분석
                </div>
                <div style="font-size: 18px; color: #536471; margin-bottom: 24px;">
                    개인화된 포트폴리오 분석을 보려면 로그인이 필요합니다
                </div>
                <div style="font-size: 14px; color: #536471; margin-bottom: 32px; max-width: 500px; line-height: 1.5;">
                    로그인 후 섹터별 수익률, 자산 추이, 개별 종목 분석 등<br>
                    상세한 포트폴리오 인사이트를 확인하세요
                </div>
                <a href="/accounts/login/" style="
                    display: inline-block;
                    background: #1d9bf0;
                    color: white;
                    padding: 16px 32px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: 600;
                    font-size: 16px;
                    transition: all 0.2s;
                    box-shadow: 0 2px 8px rgba(29, 155, 240, 0.3);
                " onmouseover="this.style.background='#1a8cd8'; this.style.transform='translateY(-2px)'" 
                   onmouseout="this.style.background='#1d9bf0'; this.style.transform='translateY(0)'">
                    로그인하고 포트폴리오 분석 보기
                </a>
            </div>
        `;
    }
    
    console.log('포트폴리오 페이지 로그인 안내 표시 완료');
}

// 포트폴리오 페이지 초기화 (로그인된 경우)
function initializePortfolioPage() {
    console.log('포트폴리오 페이지 초기화 시작');
    
    // 로그인 상태 확인 후에만 초기화
    try {
        // 1. 차트 초기화 함수들 호출
        console.log('차트 초기화 시작');
        if (typeof initializeStockPerformanceChart === 'function') {
            initializeStockPerformanceChart();
            console.log('주식 차트 초기화 완료');
        }
        if (typeof initializePropertyPerformanceChart === 'function') {
            initializePropertyPerformanceChart();
            console.log('부동산 차트 초기화 완료');
        }
        if (typeof initializeSectorReturnButtons === 'function') {
            initializeSectorReturnButtons();
            console.log('섹터 버튼 초기화 완료');
        }
        if (typeof initializePropertyReturnButtons === 'function') {
            initializePropertyReturnButtons();
            console.log('부동산 버튼 초기화 완료');
        }
        
        // 2. 이벤트 리스너 재연결
        console.log('이벤트 리스너 재연결 시작');
        reconnectPortfolioEventListeners();
        
        // 3. 포트폴리오 데이터 로드
        console.log('포트폴리오 데이터 로드 시작');
        loadPortfolioData();
        
        // 4. 기본적으로 주식 포트폴리오 표시
        console.log('기본 포트폴리오 표시 시작');
        setTimeout(() => {
            showStockPortfolio();
            console.log('기본 주식 포트폴리오 표시 완료');
        }, 200);
        
        console.log('포트폴리오 페이지 초기화 완료');
        
        // 추가 디버깅 정보
        console.log('포트폴리오 페이지 상태:');
        console.log('- 주식 포트폴리오 컨테이너:', !!document.getElementById('stockPortfolio'));
        console.log('- 부동산 포트폴리오 컨테이너:', !!document.getElementById('propertyPortfolio'));
        console.log('- 자산 타입 버튼들:', document.querySelectorAll('.asset-type-btn').length);
        console.log('- 기간 선택 버튼들:', document.querySelectorAll('.period-btn').length);
    } catch (error) {
        console.error('포트폴리오 페이지 초기화 중 오류:', error);
        // 오류 발생 시 로그인 안내 표시
        showPortfolioLoginRequired();
    }
}

// 포트폴리오 데이터 로드
async function loadPortfolioData() {
    try {
        console.log('포트폴리오 API 호출 시작');
        const response = await fetch('/dashboard/api/portfolio/?interval=weekly', {
            credentials: 'same-origin'
        });
        
        console.log('API 응답 상태:', response.status);
        
        if (response.status === 401) {
            console.log('포트폴리오 데이터 로드 실패: 로그인 필요');
            return;
        }
        
        const data = await response.json();
        console.log('포트폴리오 데이터 로드 완료:', data);
        
        // 섹터별 분해 데이터로 원형 그래프 업데이트
        if (data.sector_breakdown) {
            updateSectorPieChart(data.sector_breakdown);
        }
        
        // 지역별 분해 데이터로 부동산 원형 그래프 업데이트
        if (data.region_breakdown) {
            updateRegionPieChart(data.region_breakdown);
        }
        
        // 주식 보유 자산으로 섹터 카드 업데이트
        if (data.stock_holdings) {
            updateSectorCards(data.stock_holdings);
        } else {
            updateSectorCards();
        }
        
        // 부동산 보유 자산으로 부동산 카드 업데이트
        if (data.real_estate_holdings) {
            updatePropertyCards(data.real_estate_holdings);
        }
        
    } catch (error) {
        console.error('포트폴리오 데이터 로드 오류:', error);
    }
}

// 섹터별 원형 그래프 업데이트
function updateSectorPieChart(sectorData) {
    console.log('섹터별 원형 그래프 업데이트:', sectorData);
    
    // Chart.js가 로드되었는지 확인
    if (typeof Chart === 'undefined') {
        console.error('Chart.js가 로드되지 않았습니다');
        return;
    }
    
    const canvas = document.getElementById('stockSectorPieChart');
    if (!canvas) {
        console.log('stockSectorPieChart 캔버스를 찾을 수 없음');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
        // 기존 차트가 있다면 제거
        if (window.stockSectorPieChart && typeof window.stockSectorPieChart.destroy === 'function') {
            window.stockSectorPieChart.destroy();
        }
    
    const labels = Object.keys(sectorData);
    const values = Object.values(sectorData);
    const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'];
    
    window.stockSectorPieChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false  // 원형 그래프만 툴팁 비활성화
                },
                datalabels: {
                    display: true,
                    color: '#fff',
                    font: {
                        weight: 'bold',
                        size: 12
                    },
                    formatter: function(value, context) {
                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                        const percentage = ((value / total) * 100).toFixed(1);
                        const label = context.chart.data.labels[context.dataIndex];
                        
                        // 퍼센트가 5% 이상일 때만 표시 (너무 작은 조각은 숨김)
                        if (percentage >= 5) {
                            return `${label}\n${percentage}%`;
                        }
                        return '';
                    },
                    anchor: 'center',
                    align: 'center',
                    offset: 0,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    borderColor: '#fff',
                    borderRadius: 6,
                    borderWidth: 2,
                    padding: 6
                }
            }
        }
    });
}

// 지역별 원형 그래프 업데이트
function updateRegionPieChart(regionData) {
    console.log('지역별 원형 그래프 업데이트:', regionData);
    
    // Chart.js가 로드되었는지 확인
    if (typeof Chart === 'undefined') {
        console.error('Chart.js가 로드되지 않았습니다');
        return;
    }
    
    const canvas = document.getElementById('realEstatePieChart');
    if (!canvas) {
        console.log('realEstatePieChart 캔버스를 찾을 수 없음');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
        // 기존 차트가 있다면 제거
        if (window.realEstatePieChart && typeof window.realEstatePieChart.destroy === 'function') {
            window.realEstatePieChart.destroy();
        }
    
    const labels = Object.keys(regionData);
    const values = Object.values(regionData);
    const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'];
    
    window.realEstatePieChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false  // 원형 그래프만 툴팁 비활성화
                },
                datalabels: {
                    display: true,
                    color: '#fff',
                    font: {
                        weight: 'bold',
                        size: 12
                    },
                    formatter: function(value, context) {
                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                        const percentage = ((value / total) * 100).toFixed(1);
                        const label = context.chart.data.labels[context.dataIndex];
                        
                        // 퍼센트가 5% 이상일 때만 표시 (너무 작은 조각은 숨김)
                        if (percentage >= 5) {
                            return `${label}\n${percentage}%`;
                        }
                        return '';
                    },
                    anchor: 'center',
                    align: 'center',
                    offset: 0,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    borderColor: '#fff',
                    borderRadius: 6,
                    borderWidth: 2,
                    padding: 6
                }
            }
        }
    });
}

// API 데이터로 섹터 카드 업데이트
async function updateSectorCardsFromAPI(stockHoldings) {
    console.log('API 데이터로 섹터 카드 업데이트:', stockHoldings);
    
    const container = document.querySelector('.sector-cards-grid');
    if (!container) {
        console.log('sector-cards-grid 컨테이너를 찾을 수 없음');
        return;
    }
    
    // 섹터별로 그룹화
    const sectorGroups = {};
    stockHoldings.forEach(holding => {
        const sector = holding.sector || '기타';
        if (!sectorGroups[sector]) {
            sectorGroups[sector] = [];
        }
        sectorGroups[sector].push(holding);
    });
    
    container.innerHTML = ''; // 기존 내용 삭제
    
    // 각 섹터별로 카드 생성
    for (const sector of Object.keys(sectorGroups)) {
        const holdings = sectorGroups[sector];
        if (holdings.length === 0) continue;
        
        // 섹터별 색상
        const sectorColor = sectorColors[sector] || '#6b7280';
        
        // 섹터별 총 합산 금액 계산
        let sectorTotalValue = 0;
        
        const stocksHTML = await Promise.all(holdings.map(async (holding) => {
            // 현재 가격 가져오기
            const currentPrice = await getStockCurrentPrice(holding.ticker);
            
            // 보유 금액 계산 (수량 * 현재가격)
            const quantity = holding.quantity || 1;
            const holdingValue = quantity * currentPrice;
            sectorTotalValue += holdingValue;
            
            // 매수 가격 (market_value에서 추출)
            const purchasePrice = holding.market_value / quantity || 0;
            
            // 수익률 계산
            const returnRate = calculateReturnRate(currentPrice, purchasePrice);
            
            return `
                <div class="portfolio-item stock-item clickable" 
                     data-stock="${encodeURIComponent(holding.name)}" 
                     data-ticker="${holding.ticker || ''}"
                     onclick="navigateToStockJournal('${holding.ticker || holding.name}')">
                    <div class="portfolio-item-name">${holding.name}</div>
                    <div class="portfolio-item-details">
                        <div class="holding-value">보유금액: ${formatPrice(holdingValue)}</div>
                        <div class="current-price">현재가: ${formatPrice(currentPrice)}</div>
                        <div class="return-rate ${returnRate >= 0 ? 'positive' : 'negative'}">수익률: ${formatReturnRate(returnRate)}</div>
                    </div>
                    <div class="portfolio-item-right">
                        <div class="portfolio-item-weight">${((holdingValue / sectorTotalValue) * 100).toFixed(1)}%</div>
                        <div class="portfolio-item-return ${returnRate >= 0 ? 'positive' : 'negative'}">${formatReturnRate(returnRate)}</div>
                    </div>
                </div>
            `;
        }));
        
        const stocksHTMLString = stocksHTML.join('');
        
        // 섹터 카드 생성
        const card = document.createElement('div');
        card.className = 'sector-group';
        card.innerHTML = `
            <div class="sector-group-header">
                <div class="sector-group-title">
                    <span class="sector-indicator" style="background: ${sectorColor};"></span>
                    ${sector}
                </div>
                <div class="sector-group-summary">
                    <div class="sector-total-value">총 합산: ${formatPrice(sectorTotalValue)}</div>
                </div>
            </div>
            <div class="sector-group-content">${stocksHTMLString}</div>
        `;
        
        container.appendChild(card);
    }
    
    // 주식 클릭 리스너 재등록
    addStockClickListeners();
}

// 기본 데이터로 섹터 카드 업데이트 (기존 함수)
function updateSectorCards(stockHoldings) {
    console.log('기본 데이터로 섹터 카드 업데이트:', stockHoldings);
    
    const container = document.querySelector('.sector-cards-grid');
    if (!container) {
        console.log('sector-cards-grid 컨테이너를 찾을 수 없음');
        return;
    }
    
    // 섹터별로 그룹화
    const sectorGroups = {};
    if (stockHoldings) {
        stockHoldings.forEach(holding => {
            const sector = holding.sector;
            if (!sectorGroups[sector]) {
                sectorGroups[sector] = [];
            }
            sectorGroups[sector].push(holding);
        });
    }
    
    // 카드 HTML 생성
    let cardsHTML = '';
    Object.keys(sectorGroups).forEach(sector => {
        const holdings = sectorGroups[sector];
        const totalValue = holdings.reduce((sum, h) => sum + h.market_value, 0);
        
        cardsHTML += `
            <div class="sector-card">
                <div class="sector-header">
                    <h4>${sector}</h4>
                    <span class="sector-value">${totalValue.toLocaleString()}원</span>
                </div>
                <div class="sector-holdings">
                    ${holdings.map(holding => `
                        <div class="holding-item">
                            <span class="holding-name">${holding.name}</span>
                            <span class="holding-value">${holding.market_value.toLocaleString()}원</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    });
    
    container.innerHTML = cardsHTML;
}

// 부동산 카드 업데이트
function updatePropertyCards(realEstateHoldings) {
    console.log('부동산 카드 업데이트:', realEstateHoldings);
    
    const container = document.querySelector('.property-cards-grid');
    if (!container) {
        console.log('property-cards-grid 컨테이너를 찾을 수 없음');
        return;
    }
    
    // 카드 HTML 생성
    let cardsHTML = '';
    realEstateHoldings.forEach(holding => {
        cardsHTML += `
            <div class="property-card">
                <div class="property-header">
                    <h4>${holding.name}</h4>
                    <span class="property-value">${holding.market_value.toLocaleString()}원</span>
                </div>
                <div class="property-details">
                    <div class="property-detail">
                        <span class="detail-label">지역:</span>
                        <span class="detail-value">${holding.region}</span>
                    </div>
                    <div class="property-detail">
                        <span class="detail-label">수량:</span>
                        <span class="detail-value">${holding.quantity}개</span>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = cardsHTML;
}

// 포트폴리오 페이지 이벤트 리스너 재연결
function reconnectPortfolioEventListeners() {
    console.log('포트폴리오 이벤트 리스너 재연결 시작');
    
    // 자산 타입 버튼 이벤트 리스너 재연결 (주식/부동산)
    const assetTypeButtons = document.querySelectorAll('.asset-type-btn');
    assetTypeButtons.forEach(button => {
        // 기존 이벤트 리스너 제거
        button.replaceWith(button.cloneNode(true));
        
        // 새로운 이벤트 리스너 추가
        const newButton = document.querySelector(`[data-type="${button.getAttribute('data-type')}"]`);
        if (newButton) {
            newButton.addEventListener('click', function() {
                const assetType = this.getAttribute('data-type');
                console.log('자산 타입 버튼 클릭됨:', assetType);
                
                if (assetType === 'stock') {
                    showStockPortfolio();
                } else if (assetType === 'real_estate') {
                    showPropertyPortfolio();
                }
            });
        }
    });
    
    // 기간 선택 버튼 이벤트 리스너 재연결
    const periodButtons = document.querySelectorAll('.period-btn');
    periodButtons.forEach(button => {
        // 기존 이벤트 리스너 제거
        button.replaceWith(button.cloneNode(true));
        
        // 새로운 이벤트 리스너 추가
        const newButton = document.querySelector(`[data-period="${button.getAttribute('data-period')}"]`);
        if (newButton) {
            newButton.addEventListener('click', function() {
                const period = this.getAttribute('data-period');
                console.log('기간 선택 버튼 클릭됨:', period);
                selectPeriod(period);
            });
        }
    });
    
    console.log('포트폴리오 이벤트 리스너 재연결 완료');
}

// 주식 포트폴리오 표시 함수
function showStockPortfolio() {
    console.log('주식 포트폴리오 표시');
    
    // 주식 포트폴리오 컨테이너 표시
    const stockPortfolio = document.getElementById('stockPortfolio');
    const propertyPortfolio = document.getElementById('propertyPortfolio');
    
    if (stockPortfolio) {
        stockPortfolio.style.display = 'block';
    }
    if (propertyPortfolio) {
        propertyPortfolio.style.display = 'none';
    }
    
    // 버튼 활성화 상태 변경
    const stockButton = document.querySelector('[data-type="stock"]');
    const propertyButton = document.querySelector('[data-type="real_estate"]');
    
    if (stockButton) {
        stockButton.classList.add('active');
    }
    if (propertyButton) {
        propertyButton.classList.remove('active');
    }
    
    // 주식 차트 업데이트
    if (typeof updateStockPerformanceChart === 'function') {
        updateStockPerformanceChart('1D');
    }
}

// 부동산 포트폴리오 표시 함수
function showPropertyPortfolio() {
    console.log('부동산 포트폴리오 표시');
    
    // 부동산 포트폴리오 컨테이너 표시
    const stockPortfolio = document.getElementById('stockPortfolio');
    const propertyPortfolio = document.getElementById('propertyPortfolio');
    
    if (stockPortfolio) {
        stockPortfolio.style.display = 'none';
    }
    if (propertyPortfolio) {
        propertyPortfolio.style.display = 'block';
    }
    
    // 버튼 활성화 상태 변경
    const stockButton = document.querySelector('[data-type="stock"]');
    const propertyButton = document.querySelector('[data-type="real_estate"]');
    
    if (stockButton) {
        stockButton.classList.remove('active');
    }
    if (propertyButton) {
        propertyButton.classList.add('active');
    }
    
    // 부동산 차트 업데이트
    if (typeof updatePropertyPerformanceChart === 'function') {
        updatePropertyPerformanceChart('1D');
    }
}

// 기간 선택 함수
function selectPeriod(period) {
    console.log('기간 선택:', period);
    
    // 모든 기간 버튼에서 active 클래스 제거
    const periodButtons = document.querySelectorAll('.period-btn');
    periodButtons.forEach(button => {
        button.classList.remove('active');
    });
    
    // 선택된 버튼에 active 클래스 추가
    const selectedButton = document.querySelector(`[data-period="${period}"]`);
    if (selectedButton) {
        selectedButton.classList.add('active');
    }
    
    // 현재 표시된 차트에 따라 업데이트
    const stockChartContainer = document.getElementById('stock-chart-container');
    const propertyChartContainer = document.getElementById('property-chart-container');
    
    if (stockChartContainer && stockChartContainer.style.display !== 'none') {
        // 주식 차트가 표시된 경우
        if (typeof updateStockPerformanceChart === 'function') {
            updateStockPerformanceChart(period);
        }
    } else if (propertyChartContainer && propertyChartContainer.style.display !== 'none') {
        // 부동산 차트가 표시된 경우
        if (typeof updatePropertyPerformanceChart === 'function') {
            updatePropertyPerformanceChart(period);
        }
    }
}

// 포트폴리오 페이지 직접 접근 시 로그인 확인
async function checkPortfolioPageAccess() {
    try {
        const response = await fetch('/dashboard/api/total/?interval=weekly', {
            credentials: 'same-origin'
        });
        
        if (response.status === 401) {
            console.log('포트폴리오 페이지 직접 접근: 로그인되지 않은 사용자');
            showPortfolioLoginRequired();
            return false;
        }
        
        return true;
    } catch (error) {
        console.error('포트폴리오 페이지 접근 확인 중 오류:', error);
        showPortfolioLoginRequired();
        return false;
    }
}

// 포트폴리오 일간 차트 라벨 생성 (일봉: 1/15, 1/16, 1/17)
function generatePortfolioDailyLabels(count) {
    const labels = [];
    const now = new Date();
    
    for (let i = count - 1; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        
        const month = date.getMonth() + 1;
        const day = date.getDate();
        labels.push(`${month}/${day}`);
    }
    
    return labels;
}

// 포트폴리오 주간 차트 라벨 생성 (주봉: 1/15, 1/22, 1/29)
function generatePortfolioWeeklyLabels(count) {
    const labels = [];
    const now = new Date();
    
    for (let i = count - 1; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - (i * 7)); // 7일씩 차이
        
        const month = date.getMonth() + 1;
        const day = date.getDate();
        labels.push(`${month}/${day}`);
    }
    
    return labels;
}

// 포트폴리오 월간 차트 라벨 생성 (주봉: Week 1, Week 2, Week 3)
function generatePortfolioMonthlyLabels(count) {
    const labels = [];
    
    for (let i = 1; i <= count; i++) {
        labels.push(`Week ${i}`);
    }
    
    return labels;
}

// 포트폴리오 년간 차트 라벨 생성 (주봉: 1월, 2월, 3월)
function generatePortfolioYearlyLabels(count) {
    const labels = [];
    const monthNames = ['1월', '2월', '3월', '4월', '5월', '6월', 
                       '7월', '8월', '9월', '10월', '11월', '12월'];
    const now = new Date();
    
    for (let i = count - 1; i >= 0; i--) {
        const date = new Date(now);
        date.setMonth(date.getMonth() - i);
        labels.push(monthNames[date.getMonth()]);
    }
    
    return labels;
}

// 포트폴리오 차트 변수들
let stockPerformanceChart = null;
let propertyPerformanceChart = null;

// 현재 선택된 섹터별 수익률 기간
let currentSectorReturnPeriod = 'daily';
let currentPropertyReturnPeriod = 'daily';

// 동적 주식 데이터 관리
let dynamicStockData = {
    '기술주': [
        { name: '삼성전자', ticker: '005930.KS', weight: '35%', value: '45,000원', dailyReturn: '+1.2%', weeklyReturn: '+5.4%' },
        { name: 'SK하이닉스', ticker: '000660.KS', weight: '25%', value: '89,000원', dailyReturn: '+3.1%', weeklyReturn: '+12.3%' },
        { name: '네이버', ticker: '035420.KS', weight: '20%', value: '180,000원', dailyReturn: '-0.5%', weeklyReturn: '+2.9%' }
    ],
    '금융주': [
        { name: '삼성생명', ticker: '032830.KS', weight: '40%', value: '75,000원', dailyReturn: '+1.5%', weeklyReturn: '+4.8%' },
        { name: 'KB금융', ticker: '105560.KS', weight: '35%', value: '52,000원', dailyReturn: '-2.2%', weeklyReturn: '+7.1%' },
        { name: '신한지주', ticker: '055550.KS', weight: '25%', value: '38,000원', dailyReturn: '+1.6%', weeklyReturn: '+6.9%' }
    ],
    '헬스케어': [
        { name: '셀트리온', ticker: '068270.KS', weight: '50%', value: '165,000원', dailyReturn: '+4.2%', weeklyReturn: '+15.8%' },
        { name: '유한양행', ticker: '000100.KS', weight: '30%', value: '85,000원', dailyReturn: '+2.1%', weeklyReturn: '+8.3%' },
        { name: '종근당', ticker: '185750.KS', weight: '20%', value: '120,000원', dailyReturn: '+2.8%', weeklyReturn: '+9.7%' }
    ]
};

// 섹터별 수익률 데이터
let sectorReturnData = {
    daily: {
        '기술주': '+2.3%',
        '금융주': '-0.8%',
        '헬스케어': '+3.1%'
    },
    weekly: {
        '기술주': '+8.7%',
        '금융주': '+6.2%',
        '헬스케어': '+11.5%'
    }
};

// 주식 자산 전체 추이 차트 초기화
function initializeStockPerformanceChart() {
    // 기존 차트가 있으면 제거
    if (stockPerformanceChart) {
        stockPerformanceChart.destroy();
    }

    const ctx = document.getElementById('stockPerformanceChart');
    if (!ctx) return;

    // 주식 자산 전체 추이 데이터 (단일 라인)
    const stockLabels = generatePortfolioDailyLabels(7);  // 일봉: 1/15, 1/16, 1/17
    const stockData = {
        labels: stockLabels,
        datasets: [
            {
                label: '주식 자산 총 가치',
                data: [100000, 102500, 101800, 105200, 107800, 109500, 112300],
                borderColor: '#4f46e5',
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6
            }
        ]
    };

    stockPerformanceChart = new Chart(ctx, {
        type: 'line',
        data: stockData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false  // 단일 라인이므로 범례 숨김
                },
                tooltip: {
                    enabled: true,
                    displayColors: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#4f46e5',
                    borderWidth: 1,
                    cornerRadius: 6,
                    padding: 8,
                    callbacks: {
                        label: function(context) {
                            return '총 자산: ' + context.parsed.y.toLocaleString() + '원';
                        }
                    }
                },
                datalabels: {
                    display: false
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            size: 11
                        }
                    }
                },
                y: {
                    display: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        font: {
                            size: 11
                        },
                        callback: function(value) {
                            return value.toLocaleString() + '원';
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });

    // 기간 선택 버튼 이벤트 리스너
    initializeStockPeriodButtons();
}

// 부동산 자산 전체 추이 차트 초기화
function initializePropertyPerformanceChart() {
    // 기존 차트가 있으면 제거
    if (propertyPerformanceChart) {
        propertyPerformanceChart.destroy();
    }

    const ctx = document.getElementById('propertyPerformanceChart');
    if (!ctx) return;

    // 부동산 자산 전체 추이 데이터 (단일 라인)
    const propertyLabels = generatePortfolioDailyLabels(7);  // 일봉: 1/15, 1/16, 1/17
    const propertyData = {
        labels: propertyLabels,
        datasets: [
            {
                label: '부동산 자산 총 가치',
                data: [80000, 81200, 81800, 82500, 83100, 84000, 84800],
                borderColor: '#059669',
                backgroundColor: 'rgba(5, 150, 105, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6
            }
        ]
    };

    propertyPerformanceChart = new Chart(ctx, {
        type: 'line',
        data: propertyData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false  // 단일 라인이므로 범례 숨김
                },
                tooltip: {
                    enabled: false,
                    displayColors: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#ffffff',
                    borderWidth: 1,
                    cornerRadius: 6,
                    padding: 8,
                    callbacks: {
                        label: function(context) {
                            return '총 자산: ' + context.parsed.y.toLocaleString() + '원';
                        }
                    }
                },
                datalabels: {
                    display: false
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            size: 11
                        }
                    }
                },
                y: {
                    display: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        font: {
                            size: 11
                        },
                        callback: function(value) {
                            return value.toLocaleString() + '원';
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });

    // 기간 선택 버튼 이벤트 리스너
    initializePropertyPeriodButtons();
}

// 주식 자산 추이 차트 기간 선택 버튼 초기화
function initializeStockPeriodButtons() {
    const buttons = document.querySelectorAll('.stock-period-btn');
    // console.log('주식 기간 버튼 초기화:', buttons.length, '개 버튼 발견');
    
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            // console.log('주식 기간 버튼 클릭:', this.getAttribute('data-period'));
            buttons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            const period = this.getAttribute('data-period');
            updateStockPerformanceChart(period);
        });
    });
}

// 부동산 자산 추이 차트 기간 선택 버튼 초기화
function initializePropertyPeriodButtons() {
    const buttons = document.querySelectorAll('.property-period-btn');
    // console.log('부동산 기간 버튼 초기화:', buttons.length, '개 버튼 발견');
    
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            // console.log('부동산 기간 버튼 클릭:', this.getAttribute('data-period'));
            buttons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            const period = this.getAttribute('data-period');
            updatePropertyPerformanceChart(period);
        });
    });
}

// 섹터별 수익률 버튼 초기화
function initializeSectorReturnButtons() {
    const buttons = document.querySelectorAll('.sector-return-btn');
    
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            buttons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            currentSectorReturnPeriod = this.getAttribute('data-period');
            updateSectorCards();
        });
    });
}

// 물건별 수익률 버튼 초기화
function initializePropertyReturnButtons() {
    const buttons = document.querySelectorAll('.property-return-btn');
    
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            buttons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            currentPropertyReturnPeriod = this.getAttribute('data-period');
            updatePropertyCards();
        });
    });
}

// 주식 자산 추이 차트 데이터 업데이트
function updateStockPerformanceChart(period) {
    // console.log('주식 차트 업데이트 시작:', period);
    if (!stockPerformanceChart) {
        // console.log('주식 차트 객체가 없습니다');
        return;
    }

    let labels, data;
    
    switch(period) {
        case '1D':
            labels = generatePortfolioDailyLabels(7);  // 일봉: 1/15, 1/16, 1/17
            data = [100000, 102500, 101800, 105200, 107800, 109500, 112300];
            break;
        case '1W':
            labels = generatePortfolioWeeklyLabels(4);  // 주봉: 1/15, 1/22, 1/29
            data = [95000, 98500, 102000, 112300];
            break;
        case '1M':
            labels = generatePortfolioMonthlyLabels(4);  // 주봉: Week 1, Week 2, Week 3
            data = [80000, 85000, 95000, 112300];
            break;
        case '1Y':
            labels = generatePortfolioYearlyLabels(12);  // 주봉: 1월, 2월, 3월
            data = [60000, 65000, 70000, 75000, 80000, 85000, 90000, 95000, 100000, 105000, 110000, 112300];
            break;
        default:
            labels = generatePortfolioDailyLabels(7);
            data = [100000, 102500, 101800, 105200, 107800, 109500, 112300];
    }

    console.log('주식 차트 데이터 업데이트:', period, labels, data);
    stockPerformanceChart.data.labels = labels;
    stockPerformanceChart.data.datasets[0].data = data;
    stockPerformanceChart.update();
    console.log('주식 차트 업데이트 완료');
}

// 부동산 자산 추이 차트 데이터 업데이트
function updatePropertyPerformanceChart(period) {
    if (!propertyPerformanceChart) return;

    let labels, data;
    
    switch(period) {
        case '1D':
            labels = generatePortfolioDailyLabels(7);  // 일봉: 1/15, 1/16, 1/17
            data = [80000, 81200, 81800, 82500, 83100, 84000, 84800];
            break;
        case '1W':
            labels = generatePortfolioWeeklyLabels(4);  // 주봉: 1/15, 1/22, 1/29
            data = [78000, 80500, 82000, 84800];
            break;
        case '1M':
            labels = generatePortfolioMonthlyLabels(4);  // 주봉: Week 1, Week 2, Week 3
            data = [70000, 75000, 80000, 84800];
            break;
        case '1Y':
            labels = generatePortfolioYearlyLabels(12);  // 주봉: 1월, 2월, 3월
            data = [60000, 62000, 64000, 66000, 68000, 70000, 72000, 74000, 76000, 78000, 80000, 84800];
            break;
        default:
            labels = generatePortfolioDailyLabels(7);
            data = [80000, 81200, 81800, 82500, 83100, 84000, 84800];
    }

    console.log('부동산 차트 데이터 업데이트:', period, labels, data);
    propertyPerformanceChart.data.labels = labels;
    propertyPerformanceChart.data.datasets[0].data = data;
    propertyPerformanceChart.update();
    console.log('부동산 차트 업데이트 완료');
}

// 섹터별 카드 업데이트 (수익률 표시 포함)
// 새로운 주식 추가 함수
function addNewStock(sector, stockData) {
    // 섹터가 존재하지 않으면 생성
    if (!dynamicStockData[sector]) {
        dynamicStockData[sector] = [];
    }
    
    // 중복 주식명 체크
    const existingStock = dynamicStockData[sector].find(stock => stock.name === stockData.name);
    if (existingStock) {
        console.log(`주식 "${stockData.name}"이 이미 "${sector}" 섹터에 존재합니다.`);
        return false;
    }
    
    // 새로운 주식 추가
    dynamicStockData[sector].push(stockData);
    
    // 섹터 카드 업데이트
    updateSectorCards();
    
    console.log(`새로운 주식 "${stockData.name}"이 "${sector}" 섹터에 추가되었습니다.`);
    return true;
}

// 주식 제거 함수
function removeStock(sector, stockName) {
    if (!dynamicStockData[sector]) return false;
    
    const stockIndex = dynamicStockData[sector].findIndex(stock => stock.name === stockName);
    if (stockIndex === -1) return false;
    
    dynamicStockData[sector].splice(stockIndex, 1);
    updateSectorCards();
    
    console.log(`주식 "${stockName}"이 "${sector}" 섹터에서 제거되었습니다.`);
    return true;
}

// 섹터별 색상 매핑
const sectorColors = {
    '기술주': '#4f46e5',
    '금융주': '#059669', 
    '헬스케어': '#dc2626',
    '에너지': '#f59e0b',
    '소비재': '#8b5cf6',
    '산업재': '#06b6d4',
    '통신': '#ef4444',
    '유틸리티': '#10b981'
};

// 주식 현재 가격 캐시
const stockPriceCache = {};

// 주식 현재 가격 가져오기 (API 호출)
async function getStockCurrentPrice(ticker) {
    // 캐시에서 먼저 확인
    if (stockPriceCache[ticker]) {
        return stockPriceCache[ticker];
    }
    
    try {
        // 실제 API 호출 (예시 - 실제 API 엔드포인트로 변경 필요)
        const response = await fetch(`/api/stock/price/${ticker}/`);
        if (response.ok) {
            const data = await response.json();
            const price = data.current_price || data.price || 0;
            
            // 캐시에 저장 (5분간 유효)
            stockPriceCache[ticker] = {
                price: price,
                timestamp: Date.now()
            };
            
            return price;
        }
    } catch (error) {
        console.error(`주식 가격 조회 오류 (${ticker}):`, error);
    }
    
    // API 실패 시 기본값 반환
    return 0;
}

// 수익률 계산 (현재 가격 vs 매수 가격)
function calculateReturnRate(currentPrice, purchasePrice) {
    if (!purchasePrice || purchasePrice === 0) return 0;
    return ((currentPrice - purchasePrice) / purchasePrice) * 100;
}

// 가격 포맷팅
function formatPrice(price) {
    return price ? price.toLocaleString() + '원' : 'N/A';
}

// 수익률 포맷팅
function formatReturnRate(rate) {
    if (rate === 0) return '0.0%';
    const sign = rate > 0 ? '+' : '';
    return `${sign}${rate.toFixed(2)}%`;
}

function updateSectorCards(stockHoldings) {
    const container = document.querySelector('.sector-cards-grid');
    if (!container) return;

    container.innerHTML = ''; // 기존 내용 삭제

    // 일간/주간 수익률에 따른 데이터
    const isDaily = currentSectorReturnPeriod === 'daily';
    const returnSuffix = isDaily ? '일간' : '주간';
    
    // API 데이터가 있으면 사용, 없으면 기본 데이터 사용
    let dataToUse;
    if (stockHoldings && Array.isArray(stockHoldings)) {
        console.log('API 데이터 받음:', stockHoldings);
        console.log('첫 번째 항목 구조:', stockHoldings[0]);
        
        // API 데이터를 섹터별로 그룹화
        const sectorGroups = {};
        stockHoldings.forEach(holding => {
            const sector = holding.sector || holding.sector_name || '기타';
            if (!sectorGroups[sector]) {
                sectorGroups[sector] = [];
            }
            sectorGroups[sector].push(holding);
        });
        
        // 섹터가 없으면 모든 데이터를 '기타'로 그룹화
        if (Object.keys(sectorGroups).length === 0 || (Object.keys(sectorGroups).length === 1 && sectorGroups['기타'])) {
            console.log('섹터 정보가 없어서 모든 데이터를 기타로 그룹화');
            sectorGroups['기타'] = stockHoldings;
        }
        
        dataToUse = sectorGroups;
        console.log('API 데이터 섹터별 그룹화 완료:', dataToUse);
    } else {
        dataToUse = dynamicStockData;
        console.log('기본 데이터 사용:', dataToUse);
    }
    
    // 데이터를 기반으로 섹터 카드 생성
    const sectors = Object.keys(dataToUse);
    
    if (sectors.length === 0) {
        console.log('표시할 섹터 데이터가 없습니다');
        container.innerHTML = `
            <div class="no-data-message">
                <h3>포트폴리오 데이터가 없습니다</h3>
                <p>주식을 추가하거나 로그인하여 포트폴리오를 확인하세요.</p>
            </div>
        `;
        return;
    }
    
    for (let i = 0; i < sectors.length; i++) {
        const sector = sectors[i];
        const stocks = dataToUse[sector];
        if (stocks.length === 0) continue; // 빈 섹터는 건너뛰기
        
        // 섹터별 색상 (기본값 설정)
        const sectorColor = sectorColors[sector] || '#6b7280';
        
        // 섹터별 수익률 가져오기
        const sectorReturn = sectorReturnData[currentSectorReturnPeriod][sector] || '0.0%';
        
        // 간단한 주식 데이터 처리
        // const stockData = stocks.map((stock) => {
        //     // 현재 가격 가져오기
        //     const currentPrice = 0; // 임시로 0으로 설정
            
        //     // 보유 금액 계산 (수량 * 현재가격)
        //     const quantity = stock.quantity || 1; // 기본 수량 1
        //     const holdingValue = quantity * currentPrice;
            
        //     return {
        //         ...stock,
        //         currentPrice,
        //         quantity,
        //         holdingValue
        //     };
        // }));
        
        // 섹터별 총 합산 금액 계산 (임시로 0으로 설정)
        const sectorTotalValue = 0;
        
        const stocksHTML = stocks.map(stock => {
            // API 데이터와 기본 데이터 모두 처리
            const stockName = stock.name || stock.stock_name || 'Unknown';
            const stockTicker = stock.ticker || stock.symbol || '';
            const stockWeight = stock.weight || '0%';
            const stockValue = stock.value || stock.market_value || '0원';
            
            // 현재 기간에 맞는 수익률 선택 (API 데이터에는 없을 수 있음)
            const currentReturn = isDaily ? (stock.dailyReturn || '0.0%') : (stock.weeklyReturn || '0.0%');
            
            // 수익률에 따른 클래스 결정
            const returnValue = parseFloat(currentReturn.replace('%', ''));
            let returnClass = 'neutral';
            if (returnValue > 0) returnClass = 'positive';
            else if (returnValue < 0) returnClass = 'negative';
            
            return `
                <div class="portfolio-item stock-item clickable" 
                     data-stock="${encodeURIComponent(stockName)}" 
                     data-ticker="${stockTicker}"
                     onclick="navigateToStockJournal('${stockTicker || stockName}')">
                    <div class="portfolio-item-name">${stockName}</div>
                    <div class="portfolio-item-right">
                        <div class="portfolio-item-weight">${stockWeight}</div>
                        <div class="portfolio-item-value">${stockValue}</div>
                        <div class="portfolio-item-return ${returnClass}">${currentReturn}</div>
                    </div>
                </div>
            `;
        }));
        
        const stocksHTMLString = stocksHTML.join('');

        // 섹터 수익률에 따른 색상 클래스 결정
        const sectorReturnValue = parseFloat(sectorReturn.replace('%', ''));
        let sectorReturnClass = 'neutral';
        if (sectorReturnValue > 0) sectorReturnClass = 'positive';
        else if (sectorReturnValue < 0) sectorReturnClass = 'negative';

        const card = document.createElement('div');
        card.className = 'sector-group';
        card.innerHTML = `
            <div class="sector-group-header">
            <div class="sector-group-title">
                <span class="sector-indicator" style="background: ${sectorColor};"></span>
                    ${sector}
            </div>
                <div class="sector-group-summary">
                    <div class="sector-total-value">총 합산: ${formatPrice(sectorTotalValue)}</div>
                    <div class="sector-return ${sectorReturnClass}">${returnSuffix} ${sectorReturn}</div>
                </div>
            </div>
            <div class="sector-group-content">${stocksHTMLString}</div>
        `;
        
        container.appendChild(card);
    });
    
    // 주식 클릭 리스너 재등록
    addStockClickListeners();
}

// 주식 클릭 리스너 추가 함수
function addStockClickListeners() {
    const stockItems = document.querySelectorAll('.stock-item[data-stock]');
    const propertyItems = document.querySelectorAll('.property-item[data-property]');
    
    // 주식 카드 클릭 리스너
    stockItems.forEach(item => {
        // 기존 이벤트 리스너 제거 (중복 방지)
        item.removeEventListener('click', handleStockClick);
        
        // 새로운 이벤트 리스너 추가
        item.addEventListener('click', handleStockClick);
        
        // 커서 포인터 스타일 추가
        item.style.cursor = 'pointer';
    });
    
    // 부동산 카드 클릭 리스너
    propertyItems.forEach(item => {
        // 기존 이벤트 리스너 제거 (중복 방지)
        item.removeEventListener('click', handlePropertyClick);
        
        // 새로운 이벤트 리스너 추가
        item.addEventListener('click', handlePropertyClick);
        
        // 커서 포인터 스타일 추가
        item.style.cursor = 'pointer';
    });
}

// 주식 클릭 핸들러
function handleStockClick(event) {
    const stockName = decodeURIComponent(this.getAttribute('data-stock'));
    navigateToStockDetail(stockName);
}

// 부동산 클릭 핸들러
function handlePropertyClick(event) {
    const propertyName = decodeURIComponent(this.getAttribute('data-property'));
    navigateToPropertyDetail(propertyName);
}

// 주식 상세 페이지로 이동
function navigateToStockDetail(stockName) {
    const encodedStockName = encodeURIComponent(stockName);
    const url = `/dashboard/stock/${encodedStockName}/`;
    
    console.log(`주식 "${stockName}" 상세 페이지로 이동: ${url}`);
    window.location.href = url;
}

// 부동산 상세 페이지로 이동
function navigateToPropertyDetail(propertyName) {
    const encodedPropertyName = encodeURIComponent(propertyName);
    const url = `/dashboard/property/${encodedPropertyName}/`;
    
    console.log(`부동산 "${propertyName}" 상세 페이지로 이동: ${url}`);
    // 현재는 주식 상세 페이지로 임시 이동 (부동산 상세 페이지 미구현)
    window.location.href = `/dashboard/stock/${encodedPropertyName}/`;
}

// 새로운 섹터 추가 함수
function addNewSector(sectorName, sectorReturn = { daily: '0.0%', weekly: '0.0%' }) {
    // 섹터별 수익률 데이터에 추가
    sectorReturnData.daily[sectorName] = sectorReturn.daily;
    sectorReturnData.weekly[sectorName] = sectorReturn.weekly;
    
    // 동적 주식 데이터에 빈 배열로 초기화
    if (!dynamicStockData[sectorName]) {
        dynamicStockData[sectorName] = [];
    }
    
    console.log(`새로운 섹터 "${sectorName}"이 추가되었습니다.`);
    return true;
}

// 테스트용 주식 추가 함수 (콘솔에서 사용 가능)
window.testAddStock = function() {
    // 기존 섹터에 새로운 주식 추가 예시
    addNewStock('기술주', {
        name: 'LG전자',
        weight: '15%',
        value: '95,000원',
        dailyReturn: '+1.8%',
        weeklyReturn: '+6.2%'
    });
    
    // 새로운 섹터 생성 후 주식 추가 예시
    addNewSector('에너지', { daily: '+1.5%', weekly: '+4.2%' });
    addNewStock('에너지', {
        name: 'SK이노베이션',
        weight: '60%',
        value: '180,000원',
        dailyReturn: '+2.1%',
        weeklyReturn: '+5.8%'
    });
    addNewStock('에너지', {
        name: 'S-Oil',
        weight: '40%',
        value: '85,000원',
        dailyReturn: '+0.9%',
        weeklyReturn: '+2.6%'
    });
};

// 물건별 카드 업데이트 (수익률 표시 포함)
function updatePropertyCards() {
    const container = document.querySelector('.property-cards-grid');
    if (!container) return;

    container.innerHTML = ''; // 기존 내용 삭제

    // 일간/주간 수익률에 따른 데이터
    const isDaily = currentPropertyReturnPeriod === 'daily';
    const returnSuffix = isDaily ? '일간' : '주간';
    
    // 물건별 수익률 데이터 (일간/주간 구분)
    const propertyReturnData = {
        daily: {
            '아파트': { sector: '+1.2%', properties: { '강남구 아파트': '+1.5%', '서초구 아파트': '+0.8%' }},
            '오피스텔': { sector: '+0.8%', properties: { '마포구 오피스텔': '+0.9%', '용산구 오피스텔': '+0.6%' }},
            '빌라': { sector: '+0.5%', properties: { '성북구 빌라': '+0.7%', '마포구 빌라': '+0.3%' }}
        },
        weekly: {
            '아파트': { sector: '+4.8%', properties: { '강남구 아파트': '+5.2%', '서초구 아파트': '+4.1%' }},
            '오피스텔': { sector: '+3.2%', properties: { '마포구 오피스텔': '+3.5%', '용산구 오피스텔': '+2.7%' }},
            '빌라': { sector: '+2.1%', properties: { '성북구 빌라': '+2.8%', '마포구 빌라': '+1.4%' }}
        }
    };

    const currentData = propertyReturnData[currentPropertyReturnPeriod];
    
    const propertyData = [
        {
            propertyType: '아파트',
            color: '#059669',
            return: currentData['아파트'].sector,
            returnClass: 'positive',
            properties: [
                { name: '강남구 아파트', weight: '60%', value: '12억원', return: currentData['아파트'].properties['강남구 아파트'] },
                { name: '서초구 아파트', weight: '40%', value: '9억원', return: currentData['아파트'].properties['서초구 아파트'] }
            ]
        },
        {
            propertyType: '오피스텔',
            color: '#0284c7',
            return: currentData['오피스텔'].sector,
            returnClass: 'positive',
            properties: [
                { name: '마포구 오피스텔', weight: '70%', value: '4억원', return: currentData['오피스텔'].properties['마포구 오피스텔'] },
                { name: '용산구 오피스텔', weight: '30%', value: '3억원', return: currentData['오피스텔'].properties['용산구 오피스텔'] }
            ]
        },
        {
            propertyType: '빌라',
            color: '#ca8a04',
            return: currentData['빌라'].sector,
            returnClass: 'positive',
            properties: [
                { name: '성북구 빌라', weight: '65%', value: '2억원', return: currentData['빌라'].properties['성북구 빌라'] },
                { name: '마포구 빌라', weight: '35%', value: '1.8억원', return: currentData['빌라'].properties['마포구 빌라'] }
            ]
        }
    ];

    propertyData.forEach(propertyGroup => {
        const propertiesHTML = propertyGroup.properties.map(property => {
            // 수익률에 따른 클래스 결정
            const returnValue = parseFloat(property.return.replace('%', ''));
            let returnClass = 'neutral';
            if (returnValue > 0) returnClass = 'positive';
            else if (returnValue < 0) returnClass = 'negative';
            
            return `
                <div class="portfolio-item property-item" data-property="${encodeURIComponent(property.name)}">
                    <div class="portfolio-item-name">${property.name}</div>
                    <div class="portfolio-item-right">
                        <div class="portfolio-item-weight">${property.weight}</div>
                        <div class="portfolio-item-value">${property.value}</div>
                        <div class="portfolio-item-return ${returnClass}">${property.return}</div>
                    </div>
                </div>
            `;
        }).join('');

        // 물건별 수익률에 따른 색상 클래스 결정
        const propertyReturnValue = parseFloat(propertyGroup.return.replace('%', ''));
        let propertyReturnClass = 'neutral';
        if (propertyReturnValue > 0) propertyReturnClass = 'positive';
        else if (propertyReturnValue < 0) propertyReturnClass = 'negative';

        const card = document.createElement('div');
        card.className = 'property-group';
        card.innerHTML = `
            <div class="property-group-title">
                <span class="sector-indicator" style="background: ${propertyGroup.color};"></span>
                ${propertyGroup.propertyType} (<span class="portfolio-item-return ${propertyReturnClass}">${returnSuffix} ${propertyGroup.return}</span>)
            </div>
            <div class="property-group-content">${propertiesHTML}</div>
        `;
        
        container.appendChild(card);
    });
}

// 종목 클릭 시 journal 앱으로 이동하는 함수
function navigateToStockJournal(ticker) {
    // ticker가 비어있거나 없으면 종목명으로 대체
    if (!ticker || ticker.trim() === '') {
        console.warn('Ticker symbol not found');
        return;
    }
    
    // URL 인코딩
    const encodedTicker = encodeURIComponent(ticker);
    
    // journal 앱의 해당 종목 페이지로 이동
    // 다른 개발자가 만든 페이지 URL에 맞게 수정 필요
    const journalUrl = `/journals/stock/${encodedTicker}/`;
    
    // 새 탭에서 열기 (선택사항)
    window.open(journalUrl, '_blank');
    
    // 또는 현재 탭에서 이동
    // window.location.href = journalUrl;
}
