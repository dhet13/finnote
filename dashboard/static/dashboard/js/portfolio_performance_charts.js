// 포트폴리오 수익률 차트 관련 함수들

// 날짜 라벨 생성 함수
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

// 포트폴리오 차트 변수들
let stockPerformanceChart = null;
let propertyPerformanceChart = null;

// 현재 선택된 섹터별 수익률 기간
let currentSectorReturnPeriod = 'daily';
let currentPropertyReturnPeriod = 'daily';

// 동적 주식 데이터 관리
let dynamicStockData = {
    '기술주': [
        { name: '삼성전자', weight: '35%', value: '45,000원', dailyReturn: '+1.2%', weeklyReturn: '+5.4%' },
        { name: 'SK하이닉스', weight: '25%', value: '89,000원', dailyReturn: '+3.1%', weeklyReturn: '+12.3%' },
        { name: '네이버', weight: '20%', value: '180,000원', dailyReturn: '-0.5%', weeklyReturn: '+2.9%' }
    ],
    '금융주': [
        { name: '삼성생명', weight: '40%', value: '75,000원', dailyReturn: '+1.5%', weeklyReturn: '+4.8%' },
        { name: 'KB금융', weight: '35%', value: '52,000원', dailyReturn: '-2.2%', weeklyReturn: '+7.1%' },
        { name: '신한지주', weight: '25%', value: '38,000원', dailyReturn: '+1.6%', weeklyReturn: '+6.9%' }
    ],
    '헬스케어': [
        { name: '셀트리온', weight: '50%', value: '165,000원', dailyReturn: '+4.2%', weeklyReturn: '+15.8%' },
        { name: '유한양행', weight: '30%', value: '85,000원', dailyReturn: '+2.1%', weeklyReturn: '+8.3%' },
        { name: '종근당', weight: '20%', value: '120,000원', dailyReturn: '+2.8%', weeklyReturn: '+9.7%' }
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
    const stockLabels = generateDailyLabels(7);
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
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#ffffff',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return '총 자산: ' + context.parsed.y.toLocaleString() + '원';
                        }
                    }
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
    const propertyLabels = generateDailyLabels(7);
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
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#ffffff',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return '총 자산: ' + context.parsed.y.toLocaleString() + '원';
                        }
                    }
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
            labels = generateDailyLabels(7);
            data = [100000, 102500, 101800, 105200, 107800, 109500, 112300];
            break;
        case '1W':
            labels = generateWeekLabels(getCurrentWeek(), 4);
            data = [95000, 98500, 102000, 112300];
            break;
        case '1M':
            labels = generateMonthLabels(12);
            data = [80000, 82000, 85000, 88000, 92000, 95000, 98000, 102000, 105000, 108000, 110000, 112300];
            break;
        case '1Y':
            labels = generateYearlySequenceLabels(5);
            data = [60000, 70000, 85000, 95000, 112300];
            break;
        default:
            labels = generateDailyLabels(7);
            data = [100000, 102500, 101800, 105200, 107800, 109500, 112300];
    }

    // console.log('주식 차트 데이터 업데이트:', labels, data);
    stockPerformanceChart.data.labels = labels;
    stockPerformanceChart.data.datasets[0].data = data;
    stockPerformanceChart.update();
    // console.log('주식 차트 업데이트 완료');
}

// 부동산 자산 추이 차트 데이터 업데이트
function updatePropertyPerformanceChart(period) {
    if (!propertyPerformanceChart) return;

    let labels, data;
    
    switch(period) {
        case '1D':
            labels = generateDailyLabels(7);
            data = [80000, 81200, 81800, 82500, 83100, 84000, 84800];
            break;
        case '1W':
            labels = generateWeekLabels(getCurrentWeek(), 4);
            data = [78000, 80500, 82000, 84800];
            break;
        case '1M':
            labels = generateMonthLabels(12);
            data = [70000, 71000, 72500, 74000, 75500, 77000, 78500, 80000, 81500, 83000, 84000, 84800];
            break;
        case '1Y':
            labels = generateYearlySequenceLabels(5);
            data = [60000, 65000, 72000, 78000, 84800];
            break;
        default:
            labels = generateDailyLabels(7);
            data = [80000, 81200, 81800, 82500, 83100, 84000, 84800];
    }

    propertyPerformanceChart.data.labels = labels;
    propertyPerformanceChart.data.datasets[0].data = data;
    propertyPerformanceChart.update();
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

function updateSectorCards() {
    const container = document.querySelector('.sector-cards-grid');
    if (!container) return;

    container.innerHTML = ''; // 기존 내용 삭제

    // 일간/주간 수익률에 따른 데이터
    const isDaily = currentSectorReturnPeriod === 'daily';
    const returnSuffix = isDaily ? '일간' : '주간';
    
    // 동적 데이터를 기반으로 섹터 카드 생성
    Object.keys(dynamicStockData).forEach(sector => {
        const stocks = dynamicStockData[sector];
        if (stocks.length === 0) return; // 빈 섹터는 건너뛰기
        
        // 섹터별 색상 (기본값 설정)
        const sectorColor = sectorColors[sector] || '#6b7280';
        
        // 섹터별 수익률 가져오기
        const sectorReturn = sectorReturnData[currentSectorReturnPeriod][sector] || '0.0%';
        
        const stocksHTML = stocks.map(stock => {
            // 현재 기간에 맞는 수익률 선택
            const currentReturn = isDaily ? stock.dailyReturn : stock.weeklyReturn;
            
            // 수익률에 따른 클래스 결정
            const returnValue = parseFloat(currentReturn.replace('%', ''));
            let returnClass = 'neutral';
            if (returnValue > 0) returnClass = 'positive';
            else if (returnValue < 0) returnClass = 'negative';
            
            return `
                <div class="portfolio-item stock-item" data-stock="${encodeURIComponent(stock.name)}">
                    <div class="portfolio-item-name">${stock.name}</div>
                    <div class="portfolio-item-right">
                        <div class="portfolio-item-weight">${stock.weight}</div>
                        <div class="portfolio-item-value">${stock.value}</div>
                        <div class="portfolio-item-return ${returnClass}">${currentReturn}</div>
                    </div>
                </div>
            `;
        }).join('');

        // 섹터 수익률에 따른 색상 클래스 결정
        const sectorReturnValue = parseFloat(sectorReturn.replace('%', ''));
        let sectorReturnClass = 'neutral';
        if (sectorReturnValue > 0) sectorReturnClass = 'positive';
        else if (sectorReturnValue < 0) sectorReturnClass = 'negative';

        const card = document.createElement('div');
        card.className = 'sector-group';
        card.innerHTML = `
            <div class="sector-group-title">
                <span class="sector-indicator" style="background: ${sectorColor};"></span>
                ${sector} (<span class="portfolio-item-return ${sectorReturnClass}">${returnSuffix} ${sectorReturn}</span>)
            </div>
            <div class="sector-group-content">${stocksHTML}</div>
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
