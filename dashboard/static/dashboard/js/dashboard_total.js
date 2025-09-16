// 차트 객체를 저장할 변수를 미리 만들어 둡니다.
let miniBarChart = null;

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
        const response = await fetch(`/dashboard/api/total/?interval=${interval}`);
        const data = await response.json();

        // 2. 받아온 데이터로 카드 내용을 업데이트합니다.
        const totalValue = Number(data.total_value) || 0;
        const changePercent = Number(data.wow_change_pct) || 0;

        document.getElementById('total-asset-value').textContent = '₩ ' + totalValue.toLocaleString();
        
        const changeEl = document.getElementById('asset-change-pct');
        changeEl.textContent = `${changePercent > 0 ? '+' : ''}${changePercent.toFixed(2)}%`;
        changeEl.className = `stat-change ${changePercent >= 0 ? 'positive' : 'negative'}`;

        // 3. 막대 그래프를 그립니다.
        drawMiniBarChart(data.series);

    } catch (error) {
        console.error('카드 데이터를 불러오는 중 오류 발생:', error);
    }
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