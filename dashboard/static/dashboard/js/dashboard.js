// 차트 객체를 저장할 변수를 미리 만들어 둡니다.
let totalBarChart = null;
let dayLineChart = null;
let monthAreaChart = null;
let mainPortfolioChart = null;

// 현재 선택된 기간
let currentCardPeriod = 'daily';  // 카드뷰 기간 (daily/weekly)
let currentMainPeriod = '1D';     // 메인 차트 기간 (1D/1W/1M/1Y)
let currentPeriodRange = 30;      // 기간 선택 (일 단위)

// 페이지 로드 시 모든 차트 초기화
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    loadDashboardData();
    initializeCardPeriodButtons();
    initializeMainPeriodButtons();
    initializePeriodRangeSelector();
    
    // 동적 일간 데이터로 초기화 (일간이 기본 선택이므로)
    setTimeout(() => {
        initializeChartData();
    }, 100);
});

// 모든 차트 초기화
function initializeCharts() {
    // 총 투자 자산 막대 차트
    const totalBarCtx = document.getElementById('total-bar-chart').getContext('2d');
    totalBarChart = new Chart(totalBarCtx, {
        type: 'bar',
        data: {
            labels: generateDailyLabels(7), // 동적 라벨
            datasets: [{
                data: generateDailyData(7), // 동적 데이터
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
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#1d9bf0',
                    borderWidth: 1,
                    cornerRadius: 6,
                    displayColors: false,
                    callbacks: {
                        title: function(context) {
                            return context[0].label;
                        },
                        label: function(context) {
                            return '₩' + (context.raw * 1000).toLocaleString();
                        }
                    }
                }
            },
            scales: { 
                x: { display: false },
                y: { display: false }
            }
        }
    });

    // One Day P&L 라인 차트
    const dayLineCtx = document.getElementById('day-line-chart').getContext('2d');
    dayLineChart = new Chart(dayLineCtx, {
        type: 'line',
        data: {
            labels: generateDailyLabels(7), // 동적 라벨
            datasets: [{
                data: generateDailyData(7).map(v => v * 0.8), // 동적 데이터
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
                    enabled: true,
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#00ba7c',
                    borderWidth: 1,
                    cornerRadius: 6,
                    displayColors: false,
                    callbacks: {
                        title: function(context) {
                            return context[0].label;
                        },
                        label: function(context) {
                            return '$' + context.raw.toFixed(2);
                        }
                    }
                }
            },
            scales: { x: { display: false }, y: { display: false } }
        }
    });

    // P&L This month 영역 차트
    const monthAreaCtx = document.getElementById('month-area-chart').getContext('2d');
    monthAreaChart = new Chart(monthAreaCtx, {
        type: 'line',
        data: {
            labels: generateDailyLabels(7), // 동적 라벨
            datasets: [{
                data: generateDailyData(7).map(v => v * 1.2), // 동적 데이터
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
                    enabled: true,
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#00ba7c',
                    borderWidth: 1,
                    cornerRadius: 6,
                    displayColors: false,
                    callbacks: {
                        title: function(context) {
                            return context[0].label;
                        },
                        label: function(context) {
                            return '$' + context.raw.toFixed(2);
                        }
                    }
                }
            },
            scales: { x: { display: false }, y: { display: false } }
        }
    });

    // 메인 포트폴리오 차트
    const mainChartCtx = document.getElementById('main-portfolio-chart').getContext('2d');
    mainPortfolioChart = new Chart(mainChartCtx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            datasets: [{
                label: 'Portfolio Value',
                data: [10000, 12000, 11500, 15000, 18000, 17500, 22000, 25000, 24500, 28000, 30000, 35000],
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
                    enabled: true,
                    backgroundColor: '#4285f4',
                    titleColor: 'white',
                    bodyColor: 'white'
                }
            },
            scales: { 
                x: { 
                    display: true,
                    grid: { display: false }
                }, 
                y: { 
                    display: true,
                    grid: { color: '#f0f0f0' }
                }
            }
        }
    });
}

// 대시보드 데이터 로드
async function loadDashboardData() {
    try {
        const response = await fetch('/dashboard/api/total/?interval=weekly');
        const data = await response.json();

        const totalValue = Number(data.total_value) || 117340;
        const changePercent = Number(data.wow_change_pct) || 1.74;

        document.getElementById('total-asset-value').textContent = '₩' + (totalValue / 1000).toFixed(2) + 'k';
        
    } catch (error) {
        console.error('대시보드 데이터 로드 중 오류 발생:', error);
    }
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
            currentCardPeriod = this.getAttribute('data-card-period');
            
            // 카드뷰 차트만 업데이트
            updateCardCharts(currentCardPeriod);
        });
    });
}

// 이전 버전의 initializeMainPeriodButtons 함수는 제거됨
// 새로운 버전이 파일 하단에 있음

// 카드뷰 차트 업데이트 (일간/주간 단위만)
function updateCardCharts(period) {
    let cardLabels, cardData;
    
    if (period === 'daily') {
        // 일간 데이터 (최근 7일간의 일별 데이터)
        cardLabels = generateDailyLabels(7); // 최근 7일
        cardData = generateDailyData(7); // 일별 누적 데이터
    } else {
        // 주간 데이터 (최근 주차별 누적)
        const currentWeek = getCurrentWeek();
        cardLabels = generateWeekLabels(currentWeek, 7); // 최근 7주
        cardData = generateWeeklyData(7); // 주간별 누적 데이터
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
            // 일간: 선택된 기간만큼의 실제 날짜별 데이터
            dataPoints = Math.min(periodRange, 365); // 최대 365일
            mainLabels = generateActualDateLabels(dataPoints);
            mainData = generatePortfolioData(dataPoints, 22000, 'daily_sequence');
            break;
        case '1W':
            // 주간: 선택된 기간을 주 단위로 변환
            dataPoints = Math.min(Math.ceil(periodRange / 7), 52); // 최대 52주
            mainLabels = generateWeeklySequenceLabels(dataPoints);
            mainData = generatePortfolioData(dataPoints, 22000, 'weekly_sequence');
            break;
        case '1M':
            // 월간: 선택된 기간을 월 단위로 변환
            dataPoints = Math.min(Math.ceil(periodRange / 30), 12); // 최대 12개월
            mainLabels = generateMonthlySequenceLabels(dataPoints);
            mainData = generatePortfolioData(dataPoints, 22000, 'monthly_sequence');
            break;
        case '1Y':
            // 연간: 선택된 기간을 년 단위로 변환
            dataPoints = Math.min(Math.ceil(periodRange / 365), 12); // 최대 12년
            mainLabels = generateYearlySequenceLabels(dataPoints);
            mainData = generatePortfolioData(dataPoints, 22000, 'yearly_sequence');
            break;
        default:
            dataPoints = Math.min(periodRange, 365);
            mainLabels = generateActualDateLabels(dataPoints);
            mainData = generatePortfolioData(dataPoints, 22000, 'daily_sequence');
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
function generateDailyLabels(count) {
    const labels = [];
    const now = new Date();
    
    for (let i = count - 1; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        
        // MM/DD 형식으로 표시
        const month = date.getMonth() + 1;
        const day = date.getDate();
        labels.push(`${month}/${day}`);
    }
    
    return labels;
}

// 월별 라벨 생성
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

// 메인 차트 기간 선택 버튼 초기화 (수정된 버전)
function initializeMainPeriodButtons() {
    const mainPeriodButtons = document.querySelectorAll('.main-period-btn');
    
    mainPeriodButtons.forEach(button => {
        button.addEventListener('click', function() {
            // 모든 버튼에서 active 클래스 제거
            mainPeriodButtons.forEach(btn => btn.classList.remove('active'));
            
            // 클릭된 버튼에 active 클래스 추가
            this.classList.add('active');
            
            // 선택된 기간 업데이트
            currentMainPeriod = this.getAttribute('data-main-period');
            
            // 현재 선택된 기간 범위로 차트 업데이트
            updateMainPortfolioChart(currentMainPeriod, currentPeriodRange);
        });
    });
}

// 초기 차트 데이터도 동적으로 생성
function initializeChartData() {
    // 카드뷰 차트들은 이미 초기화 시 동적 데이터로 생성됨
    // 메인 포트폴리오 차트만 초기화 (기본 1D - 30일간)
    if (mainPortfolioChart) {
        updateMainPortfolioChart('1D', 30);
    }
}