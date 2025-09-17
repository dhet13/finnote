// 차트 객체를 저장할 변수를 미리 만들어 둡니다.
let totalBarChart = null;
let dayLineChart = null;
let monthAreaChart = null;
let mainPortfolioChart = null;
// 미니 자산 차트 인스턴스들
let stockAssetMiniChart = null;
let propertyAssetMiniChart = null;

// 현재 선택된 기간
let currentCardPeriod = 'daily';  // 카드뷰 기간 (daily/weekly)
let currentMainPeriod = '1D';     // 메인 차트 기간 (1D/1W/1M/1Y)
let currentPeriodRange = 30;      // 기간 선택 (일 단위)

// 동적 색상 팔레트 생성 함수
function generateColorPalette(count) {
    // 기본 색상 팔레트 (미리 정의된 아름다운 색상들)
    const baseColors = [
        '#4f46e5',  // 인디고
        '#059669',  // 에메랄드  
        '#dc2626',  // 레드
        '#ea580c',  // 오렌지
        '#7c3aed',  // 바이올렛
        '#0284c7',  // 스카이 블루
        '#ca8a04',  // 엠버
        '#be185d',  // 핑크
        '#7c2d12',  // 브라운
        '#065f46',  // 다크 에메랄드
        '#7c2d12',  // 다크 브라운
        '#1e40af',  // 다크 블루
        '#991b1b',  // 다크 레드
        '#a21caf',  // 다크 마젠타
        '#047857'   // 다크 그린
    ];
    
    // 필요한 개수만큼 색상 반환
    if (count <= baseColors.length) {
        return baseColors.slice(0, count);
    }
    
    // 기본 색상보다 많이 필요한 경우 HSL로 동적 생성
    const colors = [...baseColors];
    const remainingCount = count - baseColors.length;
    
    for (let i = 0; i < remainingCount; i++) {
        const hue = (360 / remainingCount) * i; // 색상환을 균등 분할
        const saturation = 65 + (Math.random() * 20); // 65-85% 채도
        const lightness = 45 + (Math.random() * 15);  // 45-60% 밝기
        colors.push(`hsl(${hue}, ${saturation}%, ${lightness}%)`);
    }
    
    return colors;
}

// 전역 초기화 함수 (base.html에서 호출됨)
let isInitializing = false; // 중복 초기화 방지

function initializeTotalPage() {
    if (isInitializing) {
        console.debug('이미 초기화 중입니다. 중복 호출 방지');
        return;
    }
    
    isInitializing = true;
    
    // 로그인 상태 확인 후 데이터 로드
    checkLoginStatusAndLoadData().then((isLoggedIn) => {
        if (isLoggedIn) {
            // 로그인된 경우에만 차트 초기화
    initializeCharts();
    initializeCardPeriodButtons();
            initializeDateRangePicker();
    initializePeriodRangeSelector();
    
            // 동적 일간 데이터로 초기화
    setTimeout(() => {
        initializeChartData();
    }, 100);
        } else {
            // 로그인되지 않은 경우 로그인 안내만 표시
            console.log('로그인되지 않은 사용자 - 차트 초기화 건너뜀');
            // 로그인 상태 주기적 확인 시작
            startLoginStatusCheck();
        }
        
        isInitializing = false;
    }).catch((error) => {
        console.error('초기화 중 오류:', error);
        isInitializing = false;
    });
}

// 로그인 상태 확인 및 데이터 로드
async function checkLoginStatusAndLoadData() {
    try {
        console.log('로그인 상태 확인 시작');
        
        // 먼저 간단한 API 호출로 로그인 상태 확인
        const response = await fetch('/dashboard/api/total/?interval=weekly', {
            credentials: 'same-origin'
        });
        
        console.log('API 응답 상태:', response.status);
        
        if (response.status === 401) {
            console.log('로그인되지 않은 사용자입니다. 로그인 안내를 표시합니다.');
            showLoginRequired();
            disablePortfolioTab(); // 포트폴리오 탭 비활성화
            return false; // 로그인되지 않음
        }
        
        if (!response.ok) {
            console.error('API 응답 오류:', response.status);
            showLoginRequired();
            disablePortfolioTab();
            return false;
        }
        
        console.log('로그인 상태 확인 완료 - 사용자 인증됨');
        
        // 로그인된 경우 데이터 로드
        await loadDashboardData();
        enablePortfolioTab(); // 포트폴리오 탭 활성화
        return true; // 로그인됨
        
    } catch (error) {
        console.error('로그인 상태 확인 중 오류:', error);
        showLoginRequired();
        disablePortfolioTab(); // 포류 발생 시 포트폴리오 탭 비활성화
        return false; // 오류 발생
    }
}

// 포트폴리오 탭 비활성화
function disablePortfolioTab() {
    const portfolioTab = document.getElementById('portfolio-tab');
    if (portfolioTab) {
        portfolioTab.style.pointerEvents = 'none';
        portfolioTab.style.opacity = '0.5';
        portfolioTab.style.cursor = 'not-allowed';
        portfolioTab.title = '로그인이 필요합니다';
        
        // 기존 클릭 이벤트 제거
        portfolioTab.replaceWith(portfolioTab.cloneNode(true));
        
        // 새로운 포트폴리오 탭 요소에 클릭 방지 이벤트 추가
        const newPortfolioTab = document.getElementById('portfolio-tab');
        if (newPortfolioTab) {
            newPortfolioTab.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                alert('포트폴리오 분석을 보려면 로그인이 필요합니다.');
                return false;
            });
        }
        
        console.log('포트폴리오 탭 비활성화 완료');
    }
}

// 포트폴리오 탭 활성화
function enablePortfolioTab() {
    const portfolioTab = document.getElementById('portfolio-tab');
    if (portfolioTab) {
        portfolioTab.style.pointerEvents = 'auto';
        portfolioTab.style.opacity = '1';
        portfolioTab.style.cursor = 'pointer';
        portfolioTab.title = '';
        
        // 기존 클릭 이벤트 제거
        portfolioTab.replaceWith(portfolioTab.cloneNode(true));
        
        // 포트폴리오 탭이 base.html의 메인 네비게이션을 사용하도록 설정
        // 포트폴리오 탭 클릭 시 메인 네비게이션의 포트폴리오 탭을 클릭하도록 함
        const newPortfolioTab = document.getElementById('portfolio-tab');
        if (newPortfolioTab) {
            newPortfolioTab.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                console.log('포트폴리오 탭 클릭됨 - 메인 네비게이션 호출');
                
                // 무한 루프 방지를 위해 직접 네비게이션 로직 실행
                console.log('포트폴리오 네비게이션 직접 실행');
                
                const tabName = 'portfolio';
                const url = '/dashboard/portfolio/';
                const contentArea = document.getElementById('dashboard-content');
                
                // 탭 활성화 상태 변경 - 모든 탭 초기화
                document.querySelectorAll('.nav-link[data-tab]').forEach(tab => {
                    tab.style.color = '#536471';
                    tab.style.fontWeight = '500';
                    tab.classList.remove('active');
                });
                
                // 포트폴리오 탭만 활성화
                this.style.color = '#1d9bf0';
                this.style.fontWeight = '600';
                this.classList.add('active');
                
                console.log('포트폴리오 탭 활성화, 자산 현황 탭 비활성화');
                
                // 로딩 표시
                contentArea.innerHTML = '<div style="text-align: center; padding: 40px; color: #536471;">로딩 중...</div>';
                
                // AJAX로 콘텐츠 로드
                fetch(url)
                    .then(response => response.text())
                    .then(html => {
                        console.log('포트폴리오 AJAX 응답 받음, HTML 길이:', html.length);
                        
                        // HTML에서 콘텐츠 영역 추출
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');
                        
                        let contentElement = doc.querySelector('.portfolio-main-content');
                        if (!contentElement) {
                            contentElement = doc.querySelector('body');
                            console.log('portfolio-main-content를 찾을 수 없어 body 사용');
                        }
                        
                        if (contentElement) {
                            contentArea.innerHTML = contentElement.outerHTML;
                            console.log('포트폴리오 콘텐츠 로드 완료');
                            
                            // 포트폴리오 페이지 초기화
                            setTimeout(() => {
                                if (typeof initializePortfolioPage === 'function') {
                                    initializePortfolioPage();
                                }
                                
                                // 포트폴리오 페이지의 자산 타입 버튼 상태 초기화
                                const stockButton = document.querySelector('[data-type="stock"]');
                                const propertyButton = document.querySelector('[data-type="real_estate"]');
                                
                                if (stockButton) {
                                    stockButton.classList.add('active');
                                }
                                if (propertyButton) {
                                    propertyButton.classList.remove('active');
                                }
                                
                                // 포트폴리오 콘텐츠 표시 상태 초기화
                                const stockPortfolio = document.getElementById('stockPortfolio');
                                const propertyPortfolio = document.getElementById('propertyPortfolio');
                                
                                if (stockPortfolio) {
                                    stockPortfolio.style.display = 'block';
                                }
                                if (propertyPortfolio) {
                                    propertyPortfolio.style.display = 'none';
                                }
                            }, 100);
                        } else {
                            contentArea.innerHTML = html;
                        }
                    })
                    .catch(error => {
                        console.error('포트폴리오 콘텐츠 로드 오류:', error);
                        contentArea.innerHTML = '<div style="text-align: center; padding: 40px; color: #dc2626;">포트폴리오 콘텐츠를 불러오는데 실패했습니다.</div>';
                    });
            });
        }
        
        console.log('포트폴리오 탭 활성화 완료');
    }
}

// 수익률 계산 함수
function generateReturnRateData(days) {
    const initialInvestment = 100000; // 초기 투자금 10만원
    const baseData = generateDailyData(days); // 기본 자산 값 데이터
    const returnRates = [];
    
    for (let i = 0; i < baseData.length; i++) {
        const currentValue = baseData[i] * 1000; // 실제 자산 값
        const returnRate = ((currentValue - initialInvestment) / initialInvestment) * 100;
        returnRates.push(parseFloat(returnRate.toFixed(2))); // 소수점 2자리까지
    }
    
    return returnRates;
}

// 누적 수익률 계산 함수 (더 현실적인 데이터)
function generateCumulativeReturnData(days) {
    const dailyReturns = [
        0.5, -0.3, 1.2, 0.8, -0.4, 1.1, 0.7, -0.2, 1.5, 0.3,
        -0.6, 0.9, 1.3, -0.1, 0.8, 1.0, -0.5, 1.4, 0.6, -0.2,
        1.1, 0.4, -0.3, 0.7, 1.2, -0.4, 0.9, 0.5, -0.1, 1.3
    ]; // 일별 수익률 변동 (%)
    
    const cumulativeReturns = [];
    let cumulative = 0;
    
    for (let i = 0; i < days; i++) {
        cumulative += dailyReturns[i % dailyReturns.length];
        cumulativeReturns.push(parseFloat(cumulative.toFixed(2)));
    }
    
    return cumulativeReturns;
}

// 모든 차트 초기화
function initializeCharts() {
    // 기존 차트들 정리 (더 안전한 체크)
    if (typeof totalBarChart !== 'undefined' && totalBarChart) {
        totalBarChart.destroy();
        totalBarChart = null;
    }
    if (typeof dayLineChart !== 'undefined' && dayLineChart) {
        dayLineChart.destroy();
        dayLineChart = null;
    }
    if (typeof monthAreaChart !== 'undefined' && monthAreaChart) {
        monthAreaChart.destroy();
        monthAreaChart = null;
    }
    if (typeof mainPortfolioChart !== 'undefined' && mainPortfolioChart) {
        mainPortfolioChart.destroy();
        mainPortfolioChart = null;
    }
    if (typeof stockAssetMiniChart !== 'undefined' && stockAssetMiniChart) {
        stockAssetMiniChart.destroy();
        stockAssetMiniChart = null;
    }
    if (typeof propertyAssetMiniChart !== 'undefined' && propertyAssetMiniChart) {
        propertyAssetMiniChart.destroy();
        propertyAssetMiniChart = null;
    }

    // 총 투자 자산 막대 차트
    const totalBarCtx = document.getElementById('totalBarChart');
    if (totalBarCtx) {
    
    // 기본 툴팁 사용 - 커스텀 툴팁 요소 생성 제거
    
    // 실제 API 데이터 사용 (없으면 더미 데이터)
    let totalChartData, totalChartLabels;
    
    if (dashboardData && dashboardData.timeseries) {
        // 실제 API 데이터 사용
        const timeseries = dashboardData.timeseries;
        totalChartData = timeseries.slice(-7).map(item => item.market_value || 0);
        totalChartLabels = generateDailyLabels(totalChartData.length);
    } else {
        // API 데이터가 없으면 빈 차트
        totalChartData = [];
        totalChartLabels = [];
    }
    
    const totalBarContext = totalBarCtx.getContext('2d');
    totalBarChart = new Chart(totalBarContext, {
        type: 'bar',
        data: {
            labels: totalChartLabels,
            datasets: [{
                data: totalChartData,
                backgroundColor: '#1d9bf0',
                borderRadius: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { display: false }, 
                tooltip: {
                    enabled: true,
                    position: 'nearest',
                    yAlign: 'top',
                    xAlign: 'center',
                    caretPadding: 10,
                    displayColors: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#1d9bf0',
                    borderWidth: 1,
                    cornerRadius: 6,
                    padding: 8,
                    external: function(context) {
                        // 툴팁을 body에 직접 추가하여 카드 밖으로 나오게 함
                        let tooltipEl = document.getElementById('chartjs-tooltip');
                        if (!tooltipEl) {
                            tooltipEl = document.createElement('div');
                            tooltipEl.id = 'chartjs-tooltip';
                            tooltipEl.style.position = 'absolute';
                            tooltipEl.style.zIndex = '999999';
                            tooltipEl.style.pointerEvents = 'none';
                            document.body.appendChild(tooltipEl);
                        }
                        
                        const {chart, tooltip} = context;
                        if (tooltip.opacity === 0) {
                            tooltipEl.style.opacity = '0';
                            return;
                        }
                        
                        tooltipEl.style.opacity = '1';
                        tooltipEl.style.left = chart.canvas.offsetLeft + tooltip.caretX + 'px';
                        tooltipEl.style.top = chart.canvas.offsetTop + tooltip.caretY - 250 + 'px';
                        tooltipEl.innerHTML = tooltip.body.map(b => b.lines.join('<br>')).join('<br>');
                    }
                },
                datalabels: {
                    display: false
                }
            },
            scales: { 
                x: { display: false },
                y: { display: false }
            }
        }
    });
    
    // 기본 툴팁 사용 - 커스텀 툴팁 이벤트 핸들러 제거

    }

    // One Day P&L 라인 차트
    const dayLineCtx = document.getElementById('dayLineChart');
    if (dayLineCtx) {
    
    const dayLineContext = dayLineCtx.getContext('2d');
    dayLineChart = new Chart(dayLineContext, {
        type: 'line',
        data: {
            labels: [], // API 데이터 사용
            datasets: [{
                data: [], // API 데이터 사용
                borderColor: '#00ba7c',
                backgroundColor: 'transparent',
                borderWidth: 2,
                pointRadius: 0,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { display: false }, 
                tooltip: { 
                    enabled: true
                }
            },
            scales: { x: { display: false }, y: { display: false } }
        }
    });

    }

    // P&L This month 영역 차트
    const monthAreaCtx = document.getElementById('monthAreaChart');
    if (monthAreaCtx) {
    
    const monthAreaContext = monthAreaCtx.getContext('2d');
    monthAreaChart = new Chart(monthAreaContext, {
        type: 'line',
        data: {
            labels: [], // API 데이터 사용
            datasets: [{
                data: [], // API 데이터 사용
                borderColor: '#00ba7c',
                backgroundColor: 'rgba(0, 186, 124, 0.1)',
                borderWidth: 2,
                fill: true,
                pointRadius: 0,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { display: false }, 
                tooltip: { 
                    enabled: true
                }
            },
            scales: { x: { display: false }, y: { display: false } }
        }
    });

    }

    // 메인 포트폴리오 차트
    const mainChartCtx = document.getElementById('mainPortfolioChart');
    if (mainChartCtx) {
    
    const mainChartContext = mainChartCtx.getContext('2d');
    // 실제 API 데이터 사용 - 누적 수익률 데이터 사용
    const timeseries = dashboardData?.timeseries || [];
    const portfolioReturnData = timeseries.map(item => {
        // 누적 수익률 데이터 사용 (cumulative_return_rate)
        return item.cumulative_return_rate || 0;
    });
    const portfolioLabels = generateDailyLabels(portfolioReturnData.length);
    
    console.log('포트폴리오 수익률 데이터:', portfolioReturnData);
    console.log('포트폴리오 라벨:', portfolioLabels);
    
    mainPortfolioChart = new Chart(mainChartContext, {
        type: 'line',
        data: {
            labels: portfolioLabels,
            datasets: [{
                label: '누적 수익률 (%)',
                data: portfolioReturnData, // 날짜별 누적 수익률 데이터
                borderColor: '#4285f4',
                backgroundColor: 'rgba(66, 133, 244, 0.1)',
                borderWidth: 3,
                fill: true,
                pointRadius: 4,
                pointBackgroundColor: '#4285f4',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { display: false },
                tooltip: { 
                    enabled: true
                },
                datalabels: {
                    display: false
                }
            },
            scales: { 
                x: { 
                    display: true,
                    grid: { display: false }
                }, 
                y: { 
                    display: true,
                    grid: { color: '#f0f0f0' },
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(1) + '%';
                        }
                    }
                }
            }
        }
    });
    }
}

// 전역 변수 선언
let stockCardData = null;
let propertyCardData = null;
let dashboardData = null;

// API 데이터에서 기간별 데이터 추출
function getApiDataForPeriod(period, dataPoints) {
    if (!dashboardData?.timeseries) {
        console.log(`getApiDataForPeriod: API 데이터 없음, ${dataPoints}개 0으로 채움`);
        return Array(dataPoints).fill(0);
    }
    
    const apiData = dashboardData.timeseries;
    const dataLength = apiData.length;
    console.log(`getApiDataForPeriod: ${period}, 요청 포인트 ${dataPoints}, API 데이터 길이 ${dataLength}`);
    console.log('API 데이터 샘플:', apiData.slice(0, 3));
    
    switch (period) {
        case '1D':
            return apiData.slice(-dataPoints).map(item => {
                const rate = item.cumulative_return_rate || 0;
                // -100% 이상의 음수 값은 0으로 처리 (데이터 오류 방지)
                return rate < -100 ? 0 : rate;
            });
        case '1W':
            const weeklyData = [];
            for (let i = 0; i < dataPoints && i * 7 < dataLength; i++) {
                const index = dataLength - 1 - (i * 7);
                if (index >= 0) {
                    const rate = apiData[index].cumulative_return_rate || 0;
                    const safeRate = rate < -100 ? 0 : rate;
                    weeklyData.unshift(safeRate);
                }
            }
            return weeklyData.length > 0 ? weeklyData : Array(dataPoints).fill(0);
        case '1M':
            const monthlyData = [];
            for (let i = 0; i < dataPoints && i * 30 < dataLength; i++) {
                const index = dataLength - 1 - (i * 30);
                if (index >= 0) {
                    const rate = apiData[index].cumulative_return_rate || 0;
                    const safeRate = rate < -100 ? 0 : rate;
                    monthlyData.unshift(safeRate);
                }
            }
            return monthlyData.length > 0 ? monthlyData : Array(dataPoints).fill(0);
        case '1Y':
            const yearlyData = [];
            for (let i = 0; i < dataPoints && i * 365 < dataLength; i++) {
                const index = dataLength - 1 - (i * 365);
                if (index >= 0) {
                    const rate = apiData[index].cumulative_return_rate || 0;
                    const safeRate = rate < -100 ? 0 : rate;
                    yearlyData.unshift(safeRate);
                }
            }
            return yearlyData.length > 0 ? yearlyData : Array(dataPoints).fill(0);
        default:
            return apiData.slice(-dataPoints).map(item => {
                const rate = item.cumulative_return_rate || 0;
                return rate < -100 ? 0 : rate;
            });
    }
}

// 대시보드 데이터 로드
async function loadDashboardData() {
    try {
        console.log('API 호출 시작: /dashboard/api/total/?interval=weekly');
        
        // API에서 데이터 로드
        const response = await fetch('/dashboard/api/total/?interval=weekly', {
            credentials: 'same-origin'  // 쿠키 포함하여 요청
        });
        
        console.log('API 응답 상태:', response.status);
        console.log('API 응답 OK:', response.ok);
        
        if (!response.ok) {
            if (response.status === 401) {
                console.warn('사용자가 로그인되지 않았습니다. 로그인 안내를 표시합니다.');
                // 로그인되지 않은 경우 로그인 안내 표시
                showLoginRequired();
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('API 응답 데이터:', data);

        if (data.status === 'error') {
            throw new Error(data.error || 'Unknown error');
        }
        
        // 전역 변수에 데이터 저장
        dashboardData = data;

        // 실제 API 응답 구조에 맞게 데이터 처리
        const holdings = data.holdings || {};
        const totalValue = Number(holdings.total_market_value) || 0;
        const totalInvested = Number(holdings.total_invested) || 0;
        const returnRate = Number(holdings.return_rate) || 0;
        const returnAmount = Number(holdings.return_amount) || 0;
        
        // 총 자산 값 업데이트
        const totalAssetElement = document.getElementById('total-asset-value');
        const totalChangeElement = document.getElementById('total-asset-change');
        
        if (totalAssetElement) {
            totalAssetElement.textContent = formatCurrency(totalValue);
        }
        
        if (totalChangeElement) {
            const changeText = returnRate >= 0 ? `+${returnRate.toFixed(1)}%` : `${returnRate.toFixed(1)}%`;
            totalChangeElement.textContent = changeText;
            totalChangeElement.style.color = returnRate >= 0 ? '#17bf63' : '#f91880';
            totalChangeElement.style.background = returnRate >= 0 ? 'rgba(23, 191, 99, 0.1)' : 'rgba(249, 24, 128, 0.1)';
        }

        // 주식과 부동산 카드 데이터 먼저 로드
        await loadCardData();

        // 자산 데이터 업데이트 (API 데이터 사용)
        updateAssetCards();
        
        // 미니 차트 직접 업데이트 (초기화 시 필수) - loadCardData 완료 후
        setTimeout(() => {
            updateStockAssetChart();
            updatePropertyAssetChart();
        }, 100);
        
        // 카드뷰 차트 업데이트 (실제 API 데이터 사용)
        updateCardCharts(currentCardPeriod);
        
    } catch (error) {
        console.error('대시보드 데이터 로드 중 오류 발생:', error);
        // 오류 발생 시 로그인 안내 표시
        showLoginRequired();
    }
}

// 카드 데이터 로드 (주식, 부동산)
async function loadCardData() {
    try {
        // 주식 데이터 로드
        const stockResponse = await fetch('/dashboard/api/stock/?interval=weekly', {
            credentials: 'same-origin'
        });
        
        if (stockResponse.ok) {
            const stockData = await stockResponse.json();
            stockCardData = stockData;
            console.log('주식 카드 데이터 로드 완료:', stockData);
        }
        
        // 부동산 데이터 로드
        const propertyResponse = await fetch('/dashboard/api/real_estate/?interval=weekly', {
            credentials: 'same-origin'
        });
        
        if (propertyResponse.ok) {
            const propertyData = await propertyResponse.json();
            propertyCardData = propertyData;
            console.log('부동산 카드 데이터 로드 완료:', propertyData);
        }
        
    } catch (error) {
        console.error('카드 데이터 로드 중 오류:', error);
        // 오류 발생 시 데이터를 null로 설정 (더미 데이터 사용 안함)
        stockCardData = null;
        propertyCardData = null;
    }
}

// 로그인되지 않은 경우 로그인 안내 표시
function showLoginRequired() {
    // 전체 통계 카드 영역을 로그인 안내로 교체
    const statsRow = document.querySelector('.stats-row');
    if (statsRow) {
        statsRow.innerHTML = `
            <div style="
                background: #f7f9fa;
                padding: 40px;
                border-radius: 8px;
                text-align: center;
                margin: 20px 0;
                width: 100%;
                max-width: 560px;
            ">
                <div style="font-size: 18px; color: #0f1419; margin-bottom: 12px; font-weight: 600;">
                    포트폴리오 데이터를 보려면 로그인이 필요합니다
                </div>
                <div style="font-size: 14px; color: #536471; margin-bottom: 24px;">
                    로그인 후 개인화된 투자 현황을 확인하세요
                </div>
                <a href="/accounts/login/" style="
                    display: inline-block;
                    background: #1d9bf0;
                    color: white;
                    padding: 12px 24px;
                    border-radius: 6px;
                    text-decoration: none;
                    font-weight: 500;
                    font-size: 14px;
                    transition: background-color 0.2s;
                " onmouseover="this.style.background='#1a8cd8'" onmouseout="this.style.background='#1d9bf0'">
                    로그인하기
                </a>
            </div>
        `;
    }
    
    // 차트 영역도 로그인 안내로 교체
    const chartSection = document.querySelector('.total-content > div[style*="background: #f7f9fa"]');
    if (chartSection) {
        chartSection.innerHTML = `
            <div style="text-align: center; padding: 60px 20px;">
                <div style="font-size: 24px; color: #0f1419; margin-bottom: 16px; font-weight: 600;">
                    📊 포트폴리오 분석
                </div>
                <div style="font-size: 16px; color: #536471; margin-bottom: 32px;">
                    로그인 후 개인화된 투자 현황과 수익률 분석을 확인하세요
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
                    transition: background-color 0.2s;
                    box-shadow: 0 2px 8px rgba(29, 155, 240, 0.3);
                " onmouseover="this.style.background='#1a8cd8'; this.style.transform='translateY(-2px)'" 
                   onmouseout="this.style.background='#1d9bf0'; this.style.transform='translateY(0)'">
                    로그인하고 포트폴리오 보기
                </a>
            </div>
        `;
    }
    
    console.log('로그인 안내 표시 완료');
}

// 카드뷰 기간 선택 버튼 초기화 (일간/주간)
function initializeCardPeriodButtons() {
    const cardPeriodButtons = document.querySelectorAll('.card-period-btn');
    
    cardPeriodButtons.forEach(button => {
        button.addEventListener('click', function() {
            // 모든 버튼에서 active 클래스 제거
            cardPeriodButtons.forEach(btn => btn.classList.remove('active'));
            
            // 클릭된 버튼에 active 클래스 추가
            this.classList.add('active');
            
            // 선택된 기간 업데이트
            const period = this.getAttribute('data-card-period');
            currentCardPeriod = period;
            
            // 자산 카드 업데이트 (새로운 함수)
            handleCardPeriodChange(period);
            
            // 기존 카드뷰 차트 업데이트
            updateCardCharts(currentCardPeriod);
        });
    });
}

// 이전 버전의 initializeMainPeriodButtons 함수는 제거됨
// 새로운 버전이 파일 하단에 있음

// 카드뷰 차트 업데이트 (일간/주간 단위만)
function updateCardCharts(period) {
    let cardLabels, cardData;
    
    // 실제 API 데이터 사용
    if (dashboardData && dashboardData.timeseries) {
        const timeseries = dashboardData.timeseries;
    
    if (period === 'daily') {
            // 일간 데이터: 최근 7일
            cardData = timeseries.slice(-7).map(item => item.market_value || 0);
            cardLabels = generateDailyLabels(cardData.length);
    } else {
            // 주간 데이터: 최근 7주 (7일씩 건너뛰기)
            const weeklyData = [];
            for (let i = 0; i < 7 && i * 7 < timeseries.length; i++) {
                const index = timeseries.length - 1 - (i * 7);
                if (index >= 0) {
                    weeklyData.unshift(timeseries[index].market_value || 0);
                }
            }
            cardData = weeklyData;
            cardLabels = generateWeeklyLabels(cardData.length);
        }
    } else {
        // API 데이터가 없으면 빈 차트
        cardLabels = [];
        cardData = [];
    }
    
    // 총 투자 자산 막대 차트 업데이트
    if (totalBarChart) {
        totalBarChart.data.labels = cardLabels;
        totalBarChart.data.datasets[0].data = cardData;
        totalBarChart.update();
    }
    
    // One Day P&L 라인 차트 업데이트
    if (dayLineChart) {
        dayLineChart.data.labels = cardLabels;
        dayLineChart.data.datasets[0].data = cardData.map(v => v * 0.8);
        dayLineChart.update();
    }
    
    // P&L This month 영역 차트 업데이트
    if (monthAreaChart) {
        monthAreaChart.data.labels = cardLabels;
        monthAreaChart.data.datasets[0].data = cardData.map(v => v * 1.2);
        monthAreaChart.update();
    }
}

// 메인 포트폴리오 차트 업데이트 (기간 선택 기반)
function updateMainPortfolioChart(period, periodRange = currentPeriodRange) {
    let mainLabels, mainData, dataPoints;
    
    switch (period) {
        case '1D':
            // 일간: 일봉 (1/15, 1/16, 1/17)
            dataPoints = Math.min(periodRange, 365); // 최대 365일
            mainLabels = generateDailyLabels(dataPoints);
            mainData = getApiDataForPeriod('1D', dataPoints);
            break;
        case '1W':
            // 주간: 주봉 (1/15, 1/22, 1/29)
            dataPoints = Math.min(Math.ceil(periodRange / 7), 52); // 최대 52주
            mainLabels = generateWeeklyLabels(dataPoints);
            mainData = getApiDataForPeriod('1W', dataPoints);
            break;
        case '1M':
            // 월간: 주봉 (Week 1, Week 2, Week 3)
            dataPoints = Math.min(Math.ceil(periodRange / 30), 12); // 최대 12개월
            mainLabels = generateMonthlyLabels(dataPoints);
            mainData = getApiDataForPeriod('1M', dataPoints);
            break;
        case '1Y':
            // 연간: 주봉 (1월, 2월, 3월)
            dataPoints = Math.min(Math.ceil(periodRange / 365), 12); // 최대 12년
            mainLabels = generateYearlyLabels(dataPoints);
            mainData = getApiDataForPeriod('1Y', dataPoints);
            break;
        case 'custom':
            // 사용자 정의 기간: 일봉 (1/15, 1/16, 1/17)
            dataPoints = Math.min(periodRange, 365);
            mainLabels = generateDailyLabels(dataPoints);
            mainData = getApiDataForPeriod('1D', dataPoints);
            break;
        default:
            dataPoints = Math.min(periodRange, 365);
            mainLabels = generateActualDateLabels(dataPoints);
            mainData = getApiDataForPeriod('1D', dataPoints);
    }
    
    // 메인 포트폴리오 차트 업데이트
    if (mainPortfolioChart) {
        mainPortfolioChart.data.labels = mainLabels;
        mainPortfolioChart.data.datasets[0].data = mainData;
        mainPortfolioChart.update();
    }
}

// 현재 주차 계산 (연도의 몇 번째 주인지)
function getCurrentWeek() {
    const now = new Date();
    const startOfYear = new Date(now.getFullYear(), 0, 1);
    const days = Math.floor((now - startOfYear) / (24 * 60 * 60 * 1000));
    return Math.ceil((days + startOfYear.getDay() + 1) / 7);
}

// 주간 라벨 생성 (현재 주차부터 역순으로 N주)
function generateWeekLabels(currentWeek, count) {
    const labels = [];
    for (let i = count - 1; i >= 0; i--) {
        const weekNum = currentWeek - i;
        if (weekNum > 0) {
            labels.push(weekNum + 'w');
        } else {
            // 작년 주차 계산
            const lastYearWeeks = 52; // 또는 53
            labels.push((lastYearWeeks + weekNum) + 'w');
        }
    }
    return labels;
}

// 주간별 누적 데이터 생성 (실제로는 API에서 가져와야 함)
function generateWeeklyData(count) {
    const data = [];
    let baseValue = 10;
    
    for (let i = 0; i < count; i++) {
        // 누적 증가하는 패턴 시뮬레이션
        baseValue += Math.random() * 10 - 2; // 약간의 변동성
        data.push(Math.max(5, Math.round(baseValue))); // 최소값 5 보장
    }
    
    return data;
}

// 시간별 라벨 생성 (카드뷰용)
function generateHourlyLabels(count) {
    const labels = [];
    const now = new Date();
    
    for (let i = count - 1; i >= 0; i--) {
        const hour = now.getHours() - i * 4; // 4시간 간격
        const adjustedHour = hour < 0 ? 24 + hour : hour;
        labels.push(String(adjustedHour).padStart(2, '0'));
    }
    
    return labels;
}

// 시간별 데이터 생성 (카드뷰용)
function generateHourlyData(count) {
    const data = [];
    let baseValue = 8;
    
    for (let i = 0; i < count; i++) {
        baseValue += Math.random() * 6 - 1; // 시간별 변동성
        data.push(Math.max(3, Math.round(baseValue)));
    }
    
    return data;
}

// 일별 데이터 생성 (카드뷰용 - 최근 7일)
function generateDailyData(count) {
    const data = [];
    let baseValue = 12;
    
    for (let i = 0; i < count; i++) {
        baseValue += Math.random() * 8 - 2; // 일별 변동성
        data.push(Math.max(5, Math.round(baseValue)));
    }
    
    return data;
}

// 상세 시간별 라벨 생성 (메인 차트용 - 24시간)
function generateDetailedHourlyLabels(count) {
    const labels = [];
    const now = new Date();
    
    for (let i = count - 1; i >= 0; i--) {
        const hour = now.getHours() - i;
        const adjustedHour = hour < 0 ? 24 + hour : hour;
        labels.push(String(adjustedHour).padStart(2, '0') + ':00');
    }
    
    return labels;
}

// 일별 라벨 생성 (날짜 형식)
// 일간 차트 라벨 생성 (일봉: 1/15, 1/16, 1/17)
function generateDailyLabels(count) {
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

// 주간 차트 라벨 생성 (주봉: 1/15, 1/22, 1/29)
function generateWeeklyLabels(count) {
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

// 월간 차트 라벨 생성 (주봉: Week 1, Week 2, Week 3)
function generateMonthlyLabels(count) {
    const labels = [];
    
    for (let i = 1; i <= count; i++) {
        labels.push(`Week ${i}`);
    }
    
    return labels;
}

// 년간 차트 라벨 생성 (주봉: 1월, 2월, 3월)
function generateYearlyLabels(count) {
    const labels = [];
    const now = new Date();
    
    for (let i = count - 1; i >= 0; i--) {
        const date = new Date(now);
        date.setMonth(date.getMonth() - i);
        const year = date.getFullYear().toString().slice(-2); // YY 형식
        const month = (date.getMonth() + 1).toString().padStart(2, '0'); // MM 형식
        labels.push(`${year}.${month}`);
    }
    
    return labels;
}

// 기존 월별 라벨 생성 (영어 월 약어)
function generateMonthLabels(count) {
    const labels = [];
    const now = new Date();
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    for (let i = count - 1; i >= 0; i--) {
        const date = new Date(now);
        date.setMonth(date.getMonth() - i);
        labels.push(monthNames[date.getMonth()]);
    }
    
    return labels;
}

// 분기별 라벨 생성
function generateQuarterLabels(count) {
    const labels = [];
    const now = new Date();
    const currentQuarter = Math.floor(now.getMonth() / 3) + 1;
    
    for (let i = count - 1; i >= 0; i--) {
        const quarter = currentQuarter - i;
        if (quarter > 0) {
            labels.push('Q' + quarter);
        } else {
            labels.push('Q' + (4 + quarter));
        }
    }
    
    return labels;
}

// 실제 날짜 라벨 생성 (12/1, 12/2, 12/3...)
function generateActualDateLabels(count) {
    const labels = [];
    const now = new Date();
    
    // 오늘부터 count일 전까지 (역순으로)
    for (let i = count - 1; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        
        const month = date.getMonth() + 1;
        const day = date.getDate();
        labels.push(`${month}/${day}`);
    }
    
    return labels;
}

// 일간 순서 라벨 생성 (1d, 2d, 3d...) - 더 이상 메인 차트에서 사용하지 않음
function generateDailySequenceLabels(count) {
    const labels = [];
    for (let i = 1; i <= count; i++) {
        labels.push(i + 'd');
    }
    return labels;
}

// 주간 순서 라벨 생성 (1w, 2w, 3w...)
function generateWeeklySequenceLabels(count) {
    const labels = [];
    for (let i = 1; i <= count; i++) {
        labels.push(i + 'w');
    }
    return labels;
}

// 월간 순서 라벨 생성 (1m, 2m, 3m...)
function generateMonthlySequenceLabels(count) {
    const labels = [];
    for (let i = 1; i <= count; i++) {
        labels.push(i + 'm');
    }
    return labels;
}

// 연간 순서 라벨 생성 (1y, 2y, 3y...)
function generateYearlySequenceLabels(count) {
    const labels = [];
    for (let i = 1; i <= count; i++) {
        labels.push(i + 'y');
    }
    return labels;
}

// 최근 월별 라벨 생성 (3M/6M/1Y용)
function generateRecentMonthlyLabels(count) {
    const labels = [];
    const now = new Date();
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    for (let i = count - 1; i >= 0; i--) {
        const date = new Date(now);
        date.setMonth(date.getMonth() - i);
        labels.push(monthNames[date.getMonth()]);
    }
    
    return labels;
}

// 포트폴리오 데이터 생성 (누적 증가 패턴)
function generatePortfolioData(count, baseValue, type) {
    const data = [];
    let currentValue = baseValue;
    
    // 타입별 변동성 설정 및 데이터 포인트 수
    let volatility, dataPoints;
    switch (type) {
        case 'daily_sequence': volatility = 800; dataPoints = count; break; // 일간 순서
        case 'weekly_sequence': volatility = 1500; dataPoints = count; break; // 주간 순서
        case 'monthly_sequence': volatility = 2500; dataPoints = count; break; // 월간 순서
        case 'yearly_sequence': volatility = 4000; dataPoints = count; break; // 연간 순서
        // 기존 타입들 (카드뷰용)
        case 'hourly': volatility = 500; dataPoints = count; break;
        case 'daily': volatility = 1000; dataPoints = count; break;
        case 'weekly': volatility = 2000; dataPoints = count; break;
        case 'monthly': volatility = 3000; dataPoints = count; break;
        case 'quarterly': volatility = 5000; dataPoints = count; break;
        default: volatility = 1000; dataPoints = count;
    }
    
    for (let i = 0; i < dataPoints; i++) {
        if (type.startsWith('single_')) {
            // 단일 데이터 포인트 (1D, 1W, 1M용)
            const variation = (Math.random() - 0.2) * volatility * 0.5;
            currentValue = baseValue + variation;
        } else {
            // 다중 데이터 포인트 (3M, 6M, 1Y용)
            const trend = (i / dataPoints) * volatility * 2;
            const variation = (Math.random() - 0.3) * volatility;
            currentValue = baseValue + trend + variation;
        }
        
        data.push(Math.max(baseValue * 0.8, Math.round(currentValue)));
    }
    
    return data;
}

// 기간 선택 드롭다운 초기화
function initializePeriodRangeSelector() {
    const periodRangeSelect = document.getElementById('period-range');
    
    if (periodRangeSelect) {
        periodRangeSelect.addEventListener('change', function() {
            currentPeriodRange = parseInt(this.value);
            // 현재 선택된 기간 타입으로 차트 업데이트
            updateMainPortfolioChart(currentMainPeriod, currentPeriodRange);
        });
    }
}

// 캘린더 기간 선택 초기화
function initializeDateRangePicker() {
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const applyBtn = document.getElementById('apply-date-range');
    const quickPeriodBtns = document.querySelectorAll('.quick-period-btn');
    
    // 요소가 존재하지 않는 경우 함수 종료
    if (!startDateInput || !endDateInput || !applyBtn) {
        console.warn('날짜 선택 요소를 찾을 수 없습니다. 로그인 안내가 표시되었을 수 있습니다.');
        return;
    }
    
    // 전역 변수로 선택된 기간 저장
    let selectedStartDate = null;
    let selectedEndDate = null;
    
    // 기본값 설정 (1D - 30일간)
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(today.getDate() - 30);
    
    startDateInput.value = thirtyDaysAgo.toISOString().split('T')[0];
    endDateInput.value = today.toISOString().split('T')[0];
    selectedStartDate = thirtyDaysAgo;
    selectedEndDate = today;
    
    // 적용 버튼 클릭 이벤트
    applyBtn.addEventListener('click', function() {
        const startDate = new Date(startDateInput.value);
        const endDate = new Date(endDateInput.value);
        
        if (startDate > endDate) {
            alert('시작 날짜는 종료 날짜보다 이전이어야 합니다.');
            return;
        }
        
        // 선택된 기간 저장
        selectedStartDate = startDate;
        selectedEndDate = endDate;
        
        // 모든 빠른 선택 버튼에서 active 클래스 제거
        quickPeriodBtns.forEach(btn => btn.classList.remove('active'));
        
        // 기간 범위 계산
        const daysDiff = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1;
        currentPeriodRange = daysDiff;
        
        // 차트 업데이트 (사용자 정의 기간)
        updateMainPortfolioChartWithCustomPeriod(selectedStartDate, selectedEndDate, daysDiff);
        
        console.log(`사용자 정의 기간: ${startDateInput.value} ~ ${endDateInput.value} (${daysDiff}일)`);
    });
    
    // 빠른 선택 버튼 클릭 이벤트 (1D/1W/1M/1Y)
    quickPeriodBtns.forEach(button => {
        // 클릭 이벤트
        button.addEventListener('click', function() {
            // 모든 버튼에서 active 클래스 제거 및 스타일 초기화
            quickPeriodBtns.forEach(btn => {
                btn.classList.remove('active');
                btn.style.background = 'transparent';
                btn.style.color = '#536471';
                btn.style.borderColor = '#eff3f4';
            });
            
            // 클릭된 버튼에 active 클래스 추가 및 스타일 적용
            this.classList.add('active');
            this.style.background = '#1d9bf0';
            this.style.color = 'white';
            this.style.borderColor = '#1d9bf0';
            
            // 선택된 기간
            const period = this.getAttribute('data-period');
            currentMainPeriod = period;
            
            // 캘린더에서 선택된 기간이 있으면 그 기간을 사용, 없으면 기본값 사용
            let startDate, endDate, days;
            
            if (selectedStartDate && selectedEndDate) {
                // 캘린더에서 선택된 기간 사용
                startDate = selectedStartDate;
                endDate = selectedEndDate;
                days = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1;
            } else {
                // 기본 기간 사용
                endDate = new Date();
                startDate = new Date();
                switch(period) {
                    case '1D':
                        startDate.setDate(endDate.getDate() - 30);
                        days = 30;
                        break;
                    case '1W':
                        startDate.setDate(endDate.getDate() - 30);
                        days = 30;
                        break;
                    case '1M':
                        startDate.setDate(endDate.getDate() - 90);
                        days = 90;
                        break;
                    case '1Y':
                        startDate.setDate(endDate.getDate() - 365);
                        days = 365;
                        break;
                    default:
                        startDate.setDate(endDate.getDate() - 7);
                        days = 7;
                }
            }
            
            currentPeriodRange = days;
            
            // 날짜 입력 필드 업데이트
            startDateInput.value = startDate.toISOString().split('T')[0];
            endDateInput.value = endDate.toISOString().split('T')[0];
            
            // 차트 업데이트 (선택된 기간에 맞춰서)
            updateMainPortfolioChartWithCustomPeriod(startDate, endDate, days, period);
            
            console.log(`빠른 선택: ${period} (${startDate.toISOString().split('T')[0]} ~ ${endDate.toISOString().split('T')[0]})`);
        });
        
        // 호버 이벤트
        button.addEventListener('mouseenter', function() {
            if (!this.classList.contains('active')) {
                this.style.background = '#f7f9fa';
                this.style.borderColor = '#cfd9de';
            }
        });
        
        button.addEventListener('mouseleave', function() {
            if (!this.classList.contains('active')) {
                this.style.background = 'transparent';
                this.style.borderColor = '#eff3f4';
            }
        });
    });
    
    // 1D 버튼을 기본 활성화
    const oneDayBtn = document.querySelector('.quick-period-btn[data-period="1D"]');
    if (oneDayBtn) {
        oneDayBtn.classList.add('active');
    }
}

// 사용자 정의 기간으로 차트 업데이트하는 함수
function updateMainPortfolioChartWithCustomPeriod(startDate, endDate, days, period = 'custom') {
    if (!mainPortfolioChart) return;
    
    let mainLabels, mainData;
    const dataPoints = Math.min(days, 365);
    
    // 기간에 따른 x축 라벨 생성
    switch(period) {
        case '1D':
            // 일봉: 1/15, 1/16, 1/17
            mainLabels = generateDailyLabelsFromDateRange(startDate, endDate);
            break;
        case '1W':
            // 주봉: 1/15, 1/22, 1/29
            mainLabels = generateWeeklyLabelsFromDateRange(startDate, endDate);
            break;
        case '1M':
            // 주차: Week 1, Week 2, Week 3
            mainLabels = generateMonthlyLabelsFromDateRange(startDate, endDate);
            break;
        case '1Y':
            // 월: 1월, 2월, 3월
            mainLabels = generateYearlyLabelsFromDateRange(startDate, endDate);
            break;
        default:
            // 사용자 정의: 일봉 형식
            mainLabels = generateDailyLabelsFromDateRange(startDate, endDate);
    }
    
    // 실제 API 데이터 사용
    if (dashboardData && dashboardData.timeseries && dashboardData.timeseries.length > 0) {
        // API 데이터에서 기간에 맞는 데이터 추출
        mainData = getApiDataForPeriod(period, mainLabels.length);
        console.log(`기간 ${period} API 데이터:`, mainData);
    } else {
        // API 데이터가 없으면 빈 차트
        mainData = Array(mainLabels.length).fill(0);
        console.log(`기간 ${period} - API 데이터 없음, 빈 차트 사용`);
    }
    
    // 메인 포트폴리오 차트 업데이트
    mainPortfolioChart.data.labels = mainLabels;
    mainPortfolioChart.data.datasets[0].data = mainData;
    mainPortfolioChart.update();
    
    console.log(`사용자 정의 차트 업데이트: ${period} (${startDate.toISOString().split('T')[0]} ~ ${endDate.toISOString().split('T')[0]})`);
}

// 날짜 범위에서 일봉 라벨 생성
function generateDailyLabelsFromDateRange(startDate, endDate) {
    const labels = [];
    const current = new Date(startDate);
    
    while (current <= endDate) {
        const month = current.getMonth() + 1;
        const day = current.getDate();
        labels.push(`${month}/${day}`);
        current.setDate(current.getDate() + 1);
    }
    
    return labels;
}

// 날짜 범위에서 주봉 라벨 생성 (7일 간격)
function generateWeeklyLabelsFromDateRange(startDate, endDate) {
    const labels = [];
    const current = new Date(startDate);
    
    while (current <= endDate) {
        const month = current.getMonth() + 1;
        const day = current.getDate();
        labels.push(`${month}/${day}`);
        current.setDate(current.getDate() + 7);
    }
    
    return labels;
}

// 날짜 범위에서 월봉 라벨 생성 (주차별)
function generateMonthlyLabelsFromDateRange(startDate, endDate) {
    const labels = [];
    const current = new Date(startDate);
    let weekCount = 1;
    
    while (current <= endDate) {
        labels.push(`Week ${weekCount}`);
        current.setDate(current.getDate() + 7);
        weekCount++;
    }
    
    return labels;
}

// 날짜 범위에서 연봉 라벨 생성 (월별) - YY.MM 형식
function generateYearlyLabelsFromDateRange(startDate, endDate) {
    const labels = [];
    const current = new Date(startDate);
    
    while (current <= endDate) {
        const year = current.getFullYear().toString().slice(-2); // YY 형식
        const month = (current.getMonth() + 1).toString().padStart(2, '0'); // MM 형식
        labels.push(`${year}.${month}`);
        current.setMonth(current.getMonth() + 1);
    }
    
    return labels;
}

// 초기 차트 데이터도 동적으로 생성
function initializeChartData() {
    // 카드뷰 차트들은 이미 초기화 시 동적 데이터로 생성됨
    // 메인 포트폴리오 차트만 초기화 (기본 1D - 30일간)
    if (mainPortfolioChart) {
        updateMainPortfolioChart('1D', 30);
    }
}

// ==================== 포트폴리오 페이지 관련 함수들 ====================

// 포트폴리오 페이지 전역 변수
let currentAssetType = 'stock';
let stockSectorChart = null;
let realEstateChart = null;

// 자산 타입 버튼 초기화 (주식/부동산)
function initializeAssetTypeButtons() {
    console.log('initializeAssetTypeButtons 함수 실행');
    
    // DOM이 완전히 로드될 때까지 재시도
    const tryInitialize = (attempt = 1, maxAttempts = 5) => {
        const buttons = document.querySelectorAll('.asset-type-btn');
        console.log(`시도 ${attempt}: 찾은 버튼 개수:`, buttons.length);
        
        if (buttons.length === 0) {
            if (attempt < maxAttempts) {
                console.log(`${attempt * 200}ms 후 재시도...`);
                setTimeout(() => tryInitialize(attempt + 1, maxAttempts), attempt * 200);
            } else {
                console.error('주식/부동산 버튼을 찾을 수 없습니다! 최대 시도 횟수 초과');
                return;
            }
        } else {
            // 버튼을 찾았으면 이벤트 리스너 등록
            buttons.forEach((button, index) => {
                console.log(`버튼 ${index + 1}:`, button.textContent.trim());
                button.addEventListener('click', function() {
                    const assetType = this.getAttribute('data-type');
                    console.log('버튼 클릭:', assetType);
                    switchAssetType(assetType);
                });
            });
            
            console.log('주식/부동산 버튼 초기화 완료');
        }
    };
    
    tryInitialize();
}

// 자산 타입 전환
function switchAssetType(assetType) {
    currentAssetType = assetType;
    
    // 버튼 스타일 변경
    document.querySelectorAll('.asset-type-btn').forEach(btn => {
        if (btn.getAttribute('data-type') === assetType) {
            btn.style.background = '#1d9bf0';
            btn.style.color = 'white';
            btn.style.border = 'none';
            btn.classList.add('active');
        } else {
            btn.style.background = 'transparent';
            btn.style.color = '#536471';
            btn.style.border = '1px solid #eff3f4';
            btn.classList.remove('active');
        }
    });
    
    // 콘텐츠 전환
    if (assetType === 'stock') {
        document.getElementById('stockPortfolio').style.display = 'block';
        document.getElementById('realEstatePortfolio').style.display = 'none';
    } else {
        document.getElementById('stockPortfolio').style.display = 'none';
        document.getElementById('realEstatePortfolio').style.display = 'block';
    }
}

// 주식 포트폴리오 초기화
function initializeStockPortfolio() {
    // 기존 차트가 있으면 제거
    if (stockSectorChart) {
        stockSectorChart.destroy();
    }

    const stockCtx = document.getElementById('stockSectorPieChart');
    if (!stockCtx) return;
    
    // 동적 데이터 (실제로는 API에서 받아올 데이터)
    // 테스트를 위해 더 많은 섹터 추가 (실제로는 API에서 동적으로 받아옴)
    const stockLabels = ['기술주', '금융주', '헬스케어', '소비재', '에너지', '통신주', '유틸리티', '소재주'];
    const stockData = [25, 20, 15, 12, 8, 10, 5, 5];
    const stockColors = generateColorPalette(stockLabels.length);

    stockSectorChart = new Chart(stockCtx.getContext('2d'), {
        type: 'pie',
        data: {
            labels: stockLabels,
            datasets: [{
                data: stockData,
                backgroundColor: stockColors,
                borderWidth: 3,
                borderColor: '#ffffff',
                hoverBorderWidth: 4,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,  // 비율 고정 해제로 크기 조정 가능
            layout: {
                padding: 10
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                },
                datalabels: {
                    display: true,
                    color: '#ffffff',
                    font: {
                        family: 'Arial, sans-serif',  // 폰트 패밀리
                        weight: '700',                // 폰트 굵기 (더 진하게)
                        size: 14                      // 폰트 크기 (더 크게)
                    },
                    formatter: function(value, context) {
                        const label = context.chart.data.labels[context.dataIndex];
                        return label + '\n' + value + '%';
                    },
                    textAlign: 'center',
                    textStrokeColor: 'rgba(0, 0, 0, 0.3)',  // 텍스트 외곽선
                    textStrokeWidth: 1
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 1500
            }
        },
        plugins: typeof ChartDataLabels !== 'undefined' ? [ChartDataLabels] : []
    });
    
    // 주식 자산 전체 추이 차트 초기화
    initializeStockPerformanceChart();
    
    // 섹터별 수익률 버튼 초기화
    initializeSectorReturnButtons();
    
    // 섹터별 카드뷰 생성 (수익률 포함)
    updateSectorCards();
}

// 부동산 포트폴리오 초기화
function initializeRealEstatePortfolio() {
    // 기존 차트가 있으면 제거
    if (realEstateChart) {
        realEstateChart.destroy();
    }

    const realEstateCtx = document.getElementById('realEstatePieChart');
    if (!realEstateCtx) return;
    
    // 동적 데이터 (실제로는 API에서 받아올 데이터)
    const realEstateLabels = ['아파트', '오피스텔', '빌라', '상가', '기타'];
    const realEstateData = [50, 25, 15, 8, 2];
    const realEstateColors = generateColorPalette(realEstateLabels.length);

    realEstateChart = new Chart(realEstateCtx.getContext('2d'), {
        type: 'pie',
        data: {
            labels: realEstateLabels,
            datasets: [{
                data: realEstateData,
                backgroundColor: realEstateColors,
                borderWidth: 3,
                borderColor: '#ffffff',
                hoverBorderWidth: 4,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,  // 비율 고정 해제로 크기 조정 가능
            layout: {
                padding: 10
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                },
                datalabels: {
                    display: true,
                    color: '#ffffff',
                    font: {
                        family: 'Arial, sans-serif',  // 폰트 패밀리
                        weight: '700',                // 폰트 굵기 (더 진하게)
                        size: 14                      // 폰트 크기 (더 크게)
                    },
                    formatter: function(value, context) {
                        const label = context.chart.data.labels[context.dataIndex];
                        return label + '\n' + value + '%';
                    },
                    textAlign: 'center',
                    textStrokeColor: 'rgba(0, 0, 0, 0.3)',  // 텍스트 외곽선
                    textStrokeWidth: 1
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 1500
            }
        },
        plugins: typeof ChartDataLabels !== 'undefined' ? [ChartDataLabels] : []
    });
    
    // 부동산 자산 전체 추이 차트 초기화
    initializePropertyPerformanceChart();
    
    // 물건별 수익률 버튼 초기화
    initializePropertyReturnButtons();
    
    // 물건별 카드뷰 생성 (수익률 포함)
    updatePropertyCards();
}

// 섹터별 카드 생성
function createSectorCards() {
    const sectorData = [
        {
            sector: '기술주',
            color: '#1d9bf0',
            stocks: [
                { name: '삼성전자', value: '₩3,500,000', return: '+12.5%', weight: '15%' },
                { name: 'SK하이닉스', value: '₩1,800,000', return: '+8.3%', weight: '8%' },
                { name: 'NAVER', value: '₩1,200,000', return: '+15.2%', weight: '6%' },
                { name: 'LG전자', value: '₩900,000', return: '+5.8%', weight: '4%' }
            ]
        },
        {
            sector: '금융주',
            color: '#17bf63',
            stocks: [
                { name: '삼성생명', value: '₩2,200,000', return: '+6.7%', weight: '10%' },
                { name: 'KB금융', value: '₩1,500,000', return: '+4.2%', weight: '7%' },
                { name: '신한지주', value: '₩1,300,000', return: '+3.8%', weight: '6%' }
            ]
        },
        {
            sector: '헬스케어',
            color: '#ffd400',
            stocks: [
                { name: '셀트리온', value: '₩1,800,000', return: '+18.5%', weight: '8%' },
                { name: '바이오니아', value: '₩1,200,000', return: '+22.1%', weight: '5%' },
                { name: '유한양행', value: '₩800,000', return: '+9.3%', weight: '4%' }
            ]
        }
    ];
    
    const container = document.querySelector('.sector-cards-grid');
    if (!container) return;
    
    container.innerHTML = '';
    
    sectorData.forEach(sector => {
        const card = document.createElement('div');
        card.className = 'sector-group';
        
        let stocksHTML = sector.stocks.map(stock => {
            const returnColor = stock.return.startsWith('+') ? '#17bf63' : '#f91880';
            return `
                <div class="portfolio-item">
                    <div>
                        <div class="portfolio-item-name">${stock.name}</div>
                        <div class="portfolio-item-weight">비중: ${stock.weight}</div>
                    </div>
                    <div class="portfolio-item-right">
                        <div class="portfolio-item-value">${stock.value}</div>
                        <div class="portfolio-item-return" style="color: ${returnColor};">${stock.return}</div>
                    </div>
                </div>
            `;
        }).join('');
        
        card.innerHTML = `
            <div class="sector-group-title">
                <span class="sector-indicator" style="background: ${sector.color};"></span>
                ${sector.sector}
            </div>
            <div class="sector-group-content">${stocksHTML}</div>
        `;
        
        container.appendChild(card);
    });
}

// 물건별 카드 생성
function createPropertyCards() {
    const propertyData = [
        {
            propertyType: '아파트',
            color: '#17bf63',
            properties: [
                { name: '대치동 래미안', value: '₩12억', return: '+8.5%', location: '강남구' },
                { name: '반포동 아크로리버파크', value: '₩15억', return: '+12.1%', location: '서초구' },
                { name: '잠실 롯데캐슬', value: '₩10억', return: '+6.8%', location: '송파구' }
            ]
        },
        {
            propertyType: '오피스텔',
            color: '#1d9bf0',
            properties: [
                { name: '역삼동 센터필드', value: '₩6억', return: '+5.2%', location: '강남구' },
                { name: '홍대 메세나폴리스', value: '₩4억', return: '+7.3%', location: '마포구' }
            ]
        },
        {
            propertyType: '빌라',
            color: '#ffd400',
            properties: [
                { name: '성수동 단독주택', value: '₩8억', return: '+4.1%', location: '성동구' },
                { name: '한남동 빌라', value: '₩5억', return: '+9.2%', location: '용산구' }
            ]
        }
    ];
    
    const container = document.querySelector('.property-cards-grid');
    if (!container) return;
    
    container.innerHTML = '';
    
    propertyData.forEach(propertyGroup => {
        const card = document.createElement('div');
        card.className = 'property-group';
        
        let propertiesHTML = propertyGroup.properties.map(property => {
            const returnColor = property.return.startsWith('+') ? '#17bf63' : '#f91880';
            return `
                <div class="portfolio-item">
                    <div>
                        <div class="portfolio-item-name">${property.name}</div>
                        <div class="portfolio-item-weight">위치: ${property.location}</div>
                    </div>
                    <div class="portfolio-item-right">
                        <div class="portfolio-item-value">${property.value}</div>
                        <div class="portfolio-item-return" style="color: ${returnColor};">${property.return}</div>
                    </div>
                </div>
            `;
        }).join('');
        
        card.innerHTML = `
            <div class="property-group-title">
                <span class="sector-indicator" style="background: ${propertyGroup.color};"></span>
                ${propertyGroup.propertyType}
            </div>
            <div class="property-group-content">${propertiesHTML}</div>
        `;
        
        container.appendChild(card);
    });
}

// 자산 데이터 관리
let assetData = {
    hasStock: true,      // 주식 자산 보유 여부
    hasProperty: true,   // 부동산 자산 보유 여부 (테스트를 위해 false로 설정)
    stock: {
        daily: { value: '82.15k', change: '+3.2%', changeValue: 3.2 },
        weekly: { value: '82.15k', change: '+8.7%', changeValue: 8.7 }
    },
    property: {
        daily: { value: '35.19k', change: '+1.8%', changeValue: 1.8 },
        weekly: { value: '35.19k', change: '+4.2%', changeValue: 4.2 }
    }
};

// 현재 선택된 기간 (일간/주간) - 이미 파일 상단에서 선언됨

// 자산 카드 업데이트 함수
function updateAssetCards() {
    const stockCard = document.getElementById('stock-asset-card');
    const propertyCard = document.getElementById('property-asset-card');
    const statsRow = document.querySelector('.stats-row');
    
    if (!statsRow) return;
    
    // 주식 자산 카드는 항상 표시
    if (stockCard) {
        stockCard.style.display = 'block';
        updateStockAssetCard();
    }
    
    // 부동산 자산 카드는 항상 표시
    if (propertyCard) {
        propertyCard.style.display = 'block';
        updatePropertyAssetCard();
    }
    
    // 카드 레이아웃 조정 (모든 카드가 항상 표시되므로 고정)
    adjustCardLayout();
}

// 주식 자산 카드 업데이트
function updateStockAssetCard() {
    const valueElement = document.getElementById('stock-asset-value');
    const changeElement = document.getElementById('stock-asset-change');
    
    // API 데이터가 있는지 확인
    if (stockCardData && stockCardData.holdings) {
        const holdings = stockCardData.holdings;
        
        // 총 시장 가치 포맷팅
        const marketValue = holdings.total_market_value || 0;
        const formattedValue = formatCurrency(marketValue);
        
        if (valueElement) {
            valueElement.textContent = formattedValue;
            valueElement.style.color = '#0f1419';
        }
        
        // 수익률 계산 및 표시
        const returnRate = holdings.return_rate || 0;
        const returnAmount = holdings.return_amount || 0;
        const formattedReturn = formatReturnRate(returnRate);
        
        if (changeElement) {
            changeElement.textContent = formattedReturn;
            changeElement.style.color = returnRate >= 0 ? '#17bf63' : '#f91880';
            changeElement.style.background = returnRate >= 0 ? 'rgba(23, 191, 99, 0.1)' : 'rgba(249, 24, 128, 0.1)';
            changeElement.style.display = 'inline-block';
        }
        
        // 주식 자산 차트 업데이트
        updateStockAssetChart();
        
        console.log('주식 자산 카드 업데이트 완료:', {
            marketValue: formattedValue,
            returnRate: formattedReturn
        });
    } else {
        // API 데이터가 없는 경우 - 하이픈 표시
        if (valueElement) {
            valueElement.textContent = '-';
            valueElement.style.color = '#536471';
        }
        
        if (changeElement) {
            changeElement.style.display = 'none';
        }
        
        // 차트 영역 비우기
        clearStockAssetChart();
        
        console.log('주식 자산 카드: API 데이터 없음');
    }
}

// 부동산 자산 카드 업데이트
function updatePropertyAssetCard() {
    const valueElement = document.getElementById('property-asset-value');
    const changeElement = document.getElementById('property-asset-change');
    
    // API 데이터가 있는지 확인
    if (propertyCardData && propertyCardData.holdings) {
        const holdings = propertyCardData.holdings;
        
        // 총 시장 가치 포맷팅
        const marketValue = holdings.total_market_value || 0;
        const formattedValue = formatCurrency(marketValue);
        
        if (valueElement) {
            valueElement.textContent = formattedValue;
            valueElement.style.color = '#0f1419';
        }
        
        // 수익률 계산 및 표시
        const returnRate = holdings.return_rate || 0;
        const returnAmount = holdings.return_amount || 0;
        const formattedReturn = formatReturnRate(returnRate);
        
        if (changeElement) {
            changeElement.textContent = formattedReturn;
            changeElement.style.color = returnRate >= 0 ? '#17bf63' : '#f91880';
            changeElement.style.background = returnRate >= 0 ? 'rgba(23, 191, 99, 0.1)' : 'rgba(249, 24, 128, 0.1)';
            changeElement.style.display = 'inline-block';
        }
        
        // 부동산 자산 차트 업데이트
        updatePropertyAssetChart();
        
        console.log('부동산 자산 카드 업데이트 완료:', {
            marketValue: formattedValue,
            returnRate: formattedReturn
        });
    } else {
        // API 데이터가 없는 경우 - 하이픈 표시
        if (valueElement) {
            valueElement.textContent = '-';
            valueElement.style.color = '#536471';
        }
        
        if (changeElement) {
            changeElement.style.display = 'none';
        }
        
        // 차트 영역 비우기
        clearPropertyAssetChart();
        
        console.log('부동산 자산 카드: API 데이터 없음');
    }
}

// 카드 레이아웃 조정
function adjustCardLayout() {
    const totalCard = document.querySelector('.stats-row .stat-card:first-child');
    const stockCard = document.getElementById('stock-asset-card');
    const propertyCard = document.getElementById('property-asset-card');
    
    // 모든 카드가 항상 표시되므로 고정 너비 적용
    const allCards = [totalCard, stockCard, propertyCard].filter(card => card);
    const cardWidth = '32%'; // 3개 카드 고정
    
    allCards.forEach(card => {
        card.style.maxWidth = cardWidth;
        card.style.width = cardWidth;
    });
}

// 자산 보유 여부 설정 함수 (테스트용)
window.setAssetAvailability = function(hasStock, hasProperty) {
    assetData.hasStock = hasStock;
    assetData.hasProperty = hasProperty;
    updateAssetCards();
    console.log(`자산 설정 변경: 주식=${hasStock}, 부동산=${hasProperty}`);
};

// 기간 변경 처리 (일간/주간 버튼)
function handleCardPeriodChange(period) {
    currentCardPeriod = period;
    updateAssetCards();
    
    // 미니 차트도 업데이트
    updateStockAssetChart();
    updatePropertyAssetChart();
    
    console.log(`카드 기간 변경: ${period}`);
}

// 자산 차트 업데이트 함수들
function updateStockAssetChart() {
    const canvas = document.getElementById('stockAssetChart');
    if (!canvas) return;
    
    // 기존 차트 제거
    if (stockAssetMiniChart) {
        stockAssetMiniChart.destroy();
        stockAssetMiniChart = null;
    }
    
    // 기본 툴팁 사용 - 커스텀 툴팁 요소 생성 제거
    
    // 실제 API 데이터 사용
    console.log('주식 카드 데이터 구조:', stockCardData);
    
    if (!stockCardData || !stockCardData.timeseries || stockCardData.timeseries.length === 0) {
        console.warn('주식 카드 데이터가 없습니다. 차트를 표시하지 않습니다.');
        // 데이터가 없으면 차트를 표시하지 않음
        return;
    }
    
    const timeseries = stockCardData.timeseries;
    const chartData = timeseries.map(item => {
        // API 응답 구조에 따라 적절한 필드명 사용
        return item.value || item.price || item.amount || item.market_value || 0;
    });
    const chartLabels = generateMiniChartLabels(chartData.length, currentCardPeriod);
    
    console.log('주식 차트 데이터:', chartData);
    console.log('주식 차트 라벨:', chartLabels);
    
    
    const ctx = canvas.getContext('2d');
    stockAssetMiniChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartLabels,
            datasets: [{
                data: chartData,
                borderColor: '#17bf63',
                backgroundColor: 'transparent',
                borderWidth: 1.5,
                pointRadius: 0,
                pointHoverRadius: 3,
                pointHoverBackgroundColor: '#17bf63',
                pointHoverBorderColor: '#ffffff',
                pointHoverBorderWidth: 2,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    enabled: true,
                    position: 'nearest',
                    yAlign: 'top',
                    xAlign: 'center',
                    caretPadding: 10,
                    displayColors: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#17bf63',
                    borderWidth: 1,
                    cornerRadius: 6,
                    padding: 8,
                    external: function(context) {
                        // 툴팁을 body에 직접 추가하여 카드 밖으로 나오게 함
                        let tooltipEl = document.getElementById('chartjs-tooltip-stock');
                        if (!tooltipEl) {
                            tooltipEl = document.createElement('div');
                            tooltipEl.id = 'chartjs-tooltip-stock';
                            tooltipEl.style.position = 'absolute';
                            tooltipEl.style.zIndex = '999999';
                            tooltipEl.style.pointerEvents = 'none';
                            tooltipEl.style.backgroundColor = 'rgba(0, 0, 0, 0.9)';
                            tooltipEl.style.color = '#ffffff';
                            tooltipEl.style.padding = '8px';
                            tooltipEl.style.borderRadius = '6px';
                            tooltipEl.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.3)';
                            tooltipEl.style.border = '1px solid #17bf63';
                            tooltipEl.style.fontSize = '12px';
                            document.body.appendChild(tooltipEl);
                        }
                        
                        const {chart, tooltip} = context;
                        if (tooltip.opacity === 0) {
                            tooltipEl.style.opacity = '0';
                            return;
                        }
                        
                        tooltipEl.style.opacity = '1';
                        tooltipEl.style.left = chart.canvas.offsetLeft + tooltip.caretX + 'px';
                        tooltipEl.style.top = chart.canvas.offsetTop + tooltip.caretY - 250 + 'px';
                        tooltipEl.innerHTML = tooltip.body.map(b => b.lines.join('<br>')).join('<br>');
                    }
                },
                datalabels: {
                    display: false
                }
            },
            scales: {
                x: { display: false },
                y: { display: false }
            },
            interaction: {
                intersect: false,
                mode: 'nearest'
            },
            hover: {
                mode: 'nearest',
                intersect: false,
                animationDuration: 400
            },
            animation: {
                duration: 600,
                easing: 'easeOutQuart'
            }
        }
    });
    
    // 기본 툴팁 사용 - 커스텀 툴팁 이벤트 핸들러 제거
}

function updatePropertyAssetChart() {
    const canvas = document.getElementById('propertyAssetChart');
    if (!canvas) return;
    
    // 기존 차트 제거
    if (propertyAssetMiniChart) {
        propertyAssetMiniChart.destroy();
        propertyAssetMiniChart = null;
    }
    
    // 기본 툴팁 사용 - 커스텀 툴팁 요소 생성 제거
    
    // 실제 API 데이터 사용
    console.log('부동산 카드 데이터 구조:', propertyCardData);
    
    if (!propertyCardData || !propertyCardData.timeseries || propertyCardData.timeseries.length === 0) {
        console.warn('부동산 카드 데이터가 없습니다. 차트를 표시하지 않습니다.');
        // 데이터가 없으면 차트를 표시하지 않음
        return;
    }
    
    const timeseries = propertyCardData.timeseries;
    const chartData = timeseries.map(item => {
        // API 응답 구조에 따라 적절한 필드명 사용
        return item.value || item.price || item.amount || item.market_value || 0;
    });
    const chartLabels = generateMiniChartLabels(chartData.length, currentCardPeriod);
    
    console.log('부동산 차트 데이터:', chartData);
    console.log('부동산 차트 라벨:', chartLabels);
    
    const ctx = canvas.getContext('2d');
    propertyAssetMiniChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartLabels,
            datasets: [{
                data: chartData,
                borderColor: '#10b981',
                backgroundColor: 'transparent',
                borderWidth: 1.5,
                pointRadius: 0,
                pointHoverRadius: 3,
                pointHoverBackgroundColor: '#10b981',
                pointHoverBorderColor: '#ffffff',
                pointHoverBorderWidth: 2,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    enabled: true,
                    position: 'nearest',
                    yAlign: 'top',
                    xAlign: 'center',
                    caretPadding: 10,
                    displayColors: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#10b981',
                    borderWidth: 1,
                    cornerRadius: 6,
                    padding: 8,
                    external: function(context) {
                        // 툴팁을 body에 직접 추가하여 카드 밖으로 나오게 함
                        let tooltipEl = document.getElementById('chartjs-tooltip-property');
                        if (!tooltipEl) {
                            tooltipEl = document.createElement('div');
                            tooltipEl.id = 'chartjs-tooltip-property';
                            tooltipEl.style.position = 'absolute';
                            tooltipEl.style.zIndex = '999999';
                            tooltipEl.style.pointerEvents = 'none';
                            tooltipEl.style.backgroundColor = 'rgba(0, 0, 0, 0.9)';
                            tooltipEl.style.color = '#ffffff';
                            tooltipEl.style.padding = '8px';
                            tooltipEl.style.borderRadius = '6px';
                            tooltipEl.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.3)';
                            tooltipEl.style.border = '1px solid #10b981';
                            tooltipEl.style.fontSize = '12px';
                            document.body.appendChild(tooltipEl);
                        }
                        
                        const {chart, tooltip} = context;
                        if (tooltip.opacity === 0) {
                            tooltipEl.style.opacity = '0';
                            return;
                        }
                        
                        tooltipEl.style.opacity = '1';
                        tooltipEl.style.left = chart.canvas.offsetLeft + tooltip.caretX + 'px';
                        tooltipEl.style.top = chart.canvas.offsetTop + tooltip.caretY - 250 + 'px';
                        tooltipEl.innerHTML = tooltip.body.map(b => b.lines.join('<br>')).join('<br>');
                    }
                },
                datalabels: {
                    display: false
                }
            },
            scales: {
                x: { display: false },
                y: { display: false }
            },
            interaction: {
                intersect: false,
                mode: 'nearest'
            },
            hover: {
                mode: 'nearest',
                intersect: false,
                animationDuration: 400
            },
            animation: {
                duration: 600,
                easing: 'easeOutQuart'
            }
        }
    });
    
    // 기본 툴팁 사용 - 커스텀 툴팁 이벤트 핸들러 제거
}

// 차트 비우기 함수들
function clearStockAssetChart() {
    if (stockAssetMiniChart) {
        stockAssetMiniChart.destroy();
        stockAssetMiniChart = null;
    }
    
    const canvas = document.getElementById('stockAssetChart');
    if (!canvas) return;
    
    // API 데이터 사용 (없으면 빈 차트)
    let chartData, chartLabels;
    
    if (stockCardData && stockCardData.timeseries) {
        // 실제 API 데이터 사용
        const timeseries = stockCardData.timeseries;
        chartData = timeseries.slice(-30).map(item => item.market_value || 0);
        chartLabels = generateMiniChartLabels(chartData.length, currentCardPeriod);
    } else {
        // API 데이터가 없으면 빈 차트
        chartData = [];
        chartLabels = [];
    }
    
    const ctx = canvas.getContext('2d');
    stockAssetMiniChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartLabels,
            datasets: [{
                data: chartData,
                borderColor: '#17bf63',
                borderWidth: 2,
                fill: false,
                pointRadius: 0,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { 
                    enabled: true,
                    position: 'nearest',
                    yAlign: 'top',
                    xAlign: 'center',
                    caretPadding: 10,
                    displayColors: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#17bf63',
                    borderWidth: 1,
                    cornerRadius: 6,
                    padding: 8,
                    external: function(context) {
                        // 툴팁을 body에 직접 추가하여 카드 밖으로 나오게 함
                        let tooltipEl = document.getElementById('chartjs-tooltip-clear');
                        if (!tooltipEl) {
                            tooltipEl = document.createElement('div');
                            tooltipEl.id = 'chartjs-tooltip-clear';
                            tooltipEl.style.position = 'absolute';
                            tooltipEl.style.zIndex = '999999';
                            tooltipEl.style.pointerEvents = 'none';
                            tooltipEl.style.backgroundColor = 'rgba(0, 0, 0, 0.9)';
                            tooltipEl.style.color = '#ffffff';
                            tooltipEl.style.padding = '8px';
                            tooltipEl.style.borderRadius = '6px';
                            tooltipEl.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.3)';
                            tooltipEl.style.border = '1px solid #17bf63';
                            tooltipEl.style.fontSize = '12px';
                            document.body.appendChild(tooltipEl);
                        }
                        
                        const {chart, tooltip} = context;
                        if (tooltip.opacity === 0) {
                            tooltipEl.style.opacity = '0';
                            return;
                        }
                        
                        tooltipEl.style.opacity = '1';
                        tooltipEl.style.left = chart.canvas.offsetLeft + tooltip.caretX + 'px';
                        tooltipEl.style.top = chart.canvas.offsetTop + tooltip.caretY - 250 + 'px';
                        tooltipEl.innerHTML = tooltip.body.map(b => b.lines.join('<br>')).join('<br>');
                    }
                }
            },
            scales: {
                x: { display: false },
                y: { display: false }
            }
        }
    });
}

function clearPropertyAssetChart() {
    if (propertyAssetMiniChart) {
        propertyAssetMiniChart.destroy();
        propertyAssetMiniChart = null;
    }
    
    const canvas = document.getElementById('propertyAssetChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // 회색 점선으로 "데이터 없음" 표시
    ctx.strokeStyle = '#d1d5db';
    ctx.setLineDash([2, 2]);
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(5, canvas.height / 2);
    ctx.lineTo(canvas.width - 5, canvas.height / 2);
    ctx.stroke();
    ctx.setLineDash([]); // 점선 해제
}

// 미니 차트용 라벨 생성 함수
function generateMiniChartLabels(count, period) {
    const labels = [];
    const now = new Date();
    
    for (let i = count - 1; i >= 0; i--) {
        const date = new Date(now);
        
        if (period === 'daily') {
            // 일간: 일봉 (1/15, 1/16, 1/17)
            date.setDate(date.getDate() - i);
            const month = date.getMonth() + 1;
            const day = date.getDate();
            labels.push(`${month}/${day}`);
        } else {
            // 주간: 주봉 (1/15, 1/22, 1/29)
            date.setDate(date.getDate() - (i * 7));
            const month = date.getMonth() + 1;
            const day = date.getDate();
            labels.push(`${month}/${day}`);
        }
    }
    
    return labels;
}

// 미니 차트 그리기 헬퍼 함수
function drawMiniChart(ctx, data, width, height, color) {
    if (data.length === 0) return;
    
    const padding = 2;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;
    
    const maxValue = Math.max(...data);
    const minValue = Math.min(...data);
    const range = maxValue - minValue || 1;
    
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    
    data.forEach((value, index) => {
        const x = padding + (index / (data.length - 1)) * chartWidth;
        const y = padding + chartHeight - ((value - minValue) / range) * chartHeight;
        
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    
    ctx.stroke();
}

// 로그인 상태 주기적 확인 (5초마다)
function startLoginStatusCheck() {
    setInterval(async () => {
        try {
            const response = await fetch('/dashboard/api/total/?interval=weekly', {
                credentials: 'same-origin'
            });
            
            if (response.status === 200) {
                // 로그인 성공 감지
                console.log('로그인 상태 감지됨. 페이지를 새로고침합니다.');
                window.location.reload();
            }
        } catch (error) {
            // 오류 무시 (로그인되지 않은 상태)
        }
    }, 5000); // 5초마다 확인
}

// 포트폴리오 페이지 전용 함수들 (중복 제거됨 - 기존 함수들 사용)

// 통화 포맷팅 함수 (통일된 형식)
function formatCurrency(amount) {
    if (amount === 0 || amount === null || amount === undefined) {
        return '0원';
    }
    
    const absAmount = Math.abs(amount);
    
    if (absAmount >= 100000000) {
        return (amount / 100000000).toFixed(1) + '억원';
    } else if (absAmount >= 10000) {
        return (amount / 10000).toFixed(1) + '만원';
    } else if (absAmount >= 1000) {
        return (amount / 1000).toFixed(1) + 'k원';
    } else {
        return Math.round(amount).toLocaleString() + '원';
    }
}

// 수익률 포맷팅 함수
function formatReturnRate(rate) {
    if (rate === 0 || rate === null || rate === undefined) {
        return '0.0%';
    }
    
    const sign = rate > 0 ? '+' : '';
    return `${sign}${rate.toFixed(2)}%`;
}

// 페이지 로드 시 자동 초기화
document.addEventListener('DOMContentLoaded', function() {
    console.log('대시보드 콘텐츠 로드됨 - 자동 초기화 시작');
    
    // 현재 경로 확인
    const currentPath = window.location.pathname;
    console.log('현재 경로:', currentPath);
    
    if (currentPath.includes('/dashboard/portfolio/')) {
        // 포트폴리오 페이지 초기화
        console.log('포트폴리오 페이지 초기화');
        if (typeof initializePortfolioPage === 'function') {
            initializePortfolioPage();
        }
    } else if (currentPath === '/dashboard/' || currentPath.includes('/dashboard/total/')) {
        // 대시보드 메인 페이지 초기화
        console.log('대시보드 메인 페이지 초기화');
        initializeTotalPage();
    }
});

// 페이지 로드 완료 후에도 초기화 (혹시 놓친 경우)
window.addEventListener('load', function() {
    console.log('페이지 완전 로드됨 - 추가 초기화 확인');
    
    const currentPath = window.location.pathname;
    if (currentPath === '/dashboard/' || currentPath.includes('/dashboard/total/')) {
        // 총자산 대시보드 차트가 초기화되지 않았다면 초기화
        if (!totalBarChart && !isInitializing) {
            console.log('차트가 초기화되지 않음 - 재초기화');
            initializeTotalPage();
        }
    } else if (currentPath.includes('/dashboard/portfolio/')) {
        // 포트폴리오 페이지는 필요 시 재초기화
        if (typeof initializePortfolioPage === 'function') {
            initializePortfolioPage();
        }
    }
});




