// 차트 객체를 저장할 변수를 미리 만들어 둡니다.
let miniBarChart = null;

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

// 페이지가 로드되면 실행될 메인 함수
document.addEventListener('DOMContentLoaded', function() {
    // 1. 기본값인 'weekly'로 데이터를 한번 불러옵니다.
    loadCardData('weekly');

    // 2. 기간 선택 버튼에 클릭 이벤트를 추가합니다.
    document.querySelectorAll('.period-controls button').forEach(button => {
        button.addEventListener('click', function() {
            // 모든 버튼에서 'active' 스타일을 제거하고, 클릭된 버튼에만 추가
            document.querySelectorAll('.period-controls button').forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // 클릭된 버튼의 data-interval 값을 가져옵니다 ('daily' 또는 'weekly')
            const selectedInterval = this.dataset.interval;
            
            // 선택된 기간으로 데이터를 다시 불러옵니다.
            loadCardData(selectedInterval);
        });
    });
});

// API를 호출하고 화면을 업데이트하는 메인 로직 함수
async function loadCardData(interval) {
    try {
        // 1. 선택된 interval을 URL 파라미터로 붙여 API에 데이터를 요청합니다.
        const response = await fetch(`/dashboard/api/total/?interval=${interval}`, {
            credentials: 'same-origin'
        });

        if (response.status === 401) {
            console.log('카드 데이터 로드 실패: 로그인 필요');
            showLoginRequired();
            return;
        }

        if (!response.ok) {
            console.error('카드 데이터 로드 실패:', response.status, response.statusText);
            showLoginRequired();
            return;
        }

        const data = await response.json();

        // 2. 받아온 데이터로 카드 내용을 업데이트합니다.
        const totalValue = Number(data.total_value) || 0;
        const changePercent = Number(data.wow_change_pct) || 0;

        document.getElementById('total-asset-value').textContent = formatCurrency(totalValue);
        
        const changeEl = document.getElementById('asset-change-pct');
        changeEl.textContent = `${changePercent > 0 ? '+' : ''}${changePercent.toFixed(2)}%`;
        changeEl.className = `stat-change ${changePercent >= 0 ? 'positive' : 'negative'}`;

        // 3. 막대 그래프를 그립니다.
        if (data.series && data.series.length > 0) {
            drawMiniBarChart(data.series);
        } else {
            // 데이터가 없으면 빈 차트 표시
            showEmptyChart();
        }

    } catch (error) {
        console.error('카드 데이터를 불러오는 중 오류 발생:', error);
        showLoginRequired();
    }
}

// 로그인 안내 표시 함수
function showLoginRequired() {
    const totalValueEl = document.getElementById('total-asset-value');
    const changeEl = document.getElementById('asset-change-pct');
    
    if (totalValueEl) {
        totalValueEl.textContent = '-';
        totalValueEl.style.color = '#536471';
    }
    
    if (changeEl) {
        changeEl.textContent = '-';
        changeEl.style.display = 'none';
    }
    
    // 빈 차트 표시
    showEmptyChart();
    
    console.log('로그인 안내 표시 완료');
}

// 빈 차트 표시 함수
function showEmptyChart() {
    const canvas = document.getElementById('mini-bar-chart');
    if (!canvas) return;
    
    // 기존 차트 제거
    if (miniBarChart) {
        miniBarChart.destroy();
        miniBarChart = null;
    }
    
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

// 막대 그래프를 그리는 함수
function drawMiniBarChart(seriesData) {
    const ctx = document.getElementById('mini-bar-chart').getContext('2d');

    // 만약 이미 차트가 그려져 있다면, 파괴하고 다시 그립니다 (중요!)
    if (miniBarChart) {
        miniBarChart.destroy();
    }

    miniBarChart = new Chart(ctx, {
        type: 'bar', // 차트 타입을 'bar'로 지정
        data: {
            labels: seriesData.map(d => d.label),
            datasets: [{
                data: seriesData.map(d => d.value),
                backgroundColor: '#1d9bf0',
                borderRadius: 4,
            }]
        },
        options: {
            // ... (차트 옵션은 이전 미니차트 예제와 유사하게 설정)
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { display: false }, 
                tooltip: { 
                    enabled: false,
                    displayColors: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#ffffff',
                    borderWidth: 1,
                    cornerRadius: 6,
                    padding: 8
                },
                datalabels: {
                    display: false
                } 
            },
            scales: { x: { display: false }, y: { display: false } }
        }
    });
}