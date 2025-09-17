console.log("✅ compose.js loaded and running!");

document.addEventListener('DOMContentLoaded', function () {

    // --- UTILITY FUNCTIONS ---
    const debounce = (func, delay = 400) => {
        let timeoutId;
        return (...args) => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    };

    // --- STATE ---
    const state = {
        selectedTicker: null,
        currentPrice: null,
        side: 'BUY',
    };

    // --- ELEMENT SELECTORS ---
    const form = document.getElementById('stock-journal-form');
    if (!form) return;

    const stockSearchInput = document.getElementById('stock-search');
    const searchResultsContainer = document.getElementById('stock-search-results');
    const selectedStockCardContainer = document.getElementById('selected-stock-card');
    const holdingSummaryCard = document.getElementById('holding-summary-card');
    
    const tradePriceInput = document.getElementById('trade-price');
    const tradeQuantityInput = document.getElementById('trade-quantity');
    const tradeDateInput = document.getElementById('trade-date');
    const tradeInputLabels = document.querySelectorAll('.trade-input-grid label');

    const buyButton = form.querySelector('.btn-buy');
    const sellButton = form.querySelector('.btn-sell');

    const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;

    // 목표/손절 가격 및 퍼센트 입력 필드
    const targetPriceInput = document.getElementById('target-price');
    const targetPercentInput = document.getElementById('target-percent');
    const stopPriceInput = document.getElementById('stop-price');
    const stopPercentInput = document.getElementById('stop-percent');

    // 매매 이유 입력 필드
    const tradeReasonInput = document.getElementById('trade-reason');

    // 매매 종료 버튼
    const completeJournalButton = document.getElementById('complete-journal-btn');

    // --- RENDER FUNCTIONS ---

    let stockChart = null; // Chart.js 인스턴스를 저장할 변수

    // 주식 이력 차트를 렌더링하는 함수
    async function renderStockHistoryChart(ticker) {
        const chartCanvas = document.getElementById('stock-history-chart');
        if (!chartCanvas) {
            console.error('Chart canvas not found.');
            return;
        }

        try {
            const response = await fetch(`/api/stock/${ticker}/history/`);
            if (!response.ok) throw new Error('Failed to fetch stock history.');
            const data = await response.json();

            const labels = data.history.map(item => item.Date);
            const prices = data.history.map(item => item.Close);

            // 기존 차트가 있다면 파괴
            if (stockChart) {
                stockChart.destroy();
            }

            const ctx = chartCanvas.getContext('2d');
            stockChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Close Price',
                        data: prices,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1,
                        fill: false,
                        pointRadius: 0, // 점 숨기기
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false, // 부모 요소에 맞춰 크기 조절
                    plugins: {
                        legend: {
                            display: false // 범례 숨기기
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                        }
                    },
                    scales: {
                        x: {
                            display: false // X축 숨기기
                        },
                        y: {
                            display: false // Y축 숨기기
                        }
                    }
                }
            });

        } catch (error) {
            console.error('Error fetching or rendering stock history:', error);
        }
    }

    function renderSelectedStockCard(data) {
        state.selectedTicker = data.ticker;
        state.currentPrice = parseFloat(data.price);

        // Parse change_percent to float here
        const parsedChangePercent = parseFloat(data.change_percent);

        const changeClass = parsedChangePercent >= 0 ? 'positive' : 'negative';
        selectedStockCardContainer.innerHTML = `
            <div class="stock-card-display">
                <div class="stock-logo" style="background-image: url(${data.logo_url})"></div>
                <div class="stock-info">
                    <div class="stock-ticker">${data.ticker}</div>
                    <div class="stock-name">${data.stock_name}</div>
                </div>
                <div class="stock-price-info">
                    <div class="stock-price">${data.price}</div>
                    <div class="stock-change ${changeClass}">${parsedChangePercent.toFixed(2)}%</div>
                </div>
                <div class="stock-sparkline">
                    <canvas id="stock-history-chart"></canvas>
                </div>
            </div>
        `;
        selectedStockCardContainer.classList.remove('hidden');
        tradePriceInput.value = state.currentPrice.toFixed(2);

        // 주식 이력 차트 렌더링 호출
        renderStockHistoryChart(data.ticker);
    }

    async function updateHoldingsDisplay(ticker) {
        try {
            const response = await fetch(`/api/stock/portfolio-summary/?ticker=${encodeURIComponent(ticker)}`);
            const data = await response.json();
            if (response.ok && data.status !== 'new') {
                const returnRate = data.return_rate || 0;
                holdingSummaryCard.innerHTML = `
                    <div class="holding-item shares">보유 주식: <strong>${data.net_quantity || 0}주</strong></div>
                    <div class="holding-item pnl">수익률(+): <strong>${returnRate >= 0 ? '+' : ''}${returnRate.toFixed(2)}%</strong></div>
                    <div class="holding-item">평균 매수 가격: <strong>${(data.average_buy_price || 0).toFixed(2)}</strong></div>
                    <div class="holding-item">평균 매도 가격: <strong>${(data.average_sell_price || 0).toFixed(2)}</strong></div>
                `;
                holdingSummaryCard.classList.remove('hidden');

                // Conditional display of "매매 종료" button
                // 보유 주식이 0이고, 저널 상태가 'completed'일 때만 버튼을 표시
                if (parseFloat(data.net_quantity) === 0 && data.status === 'completed') {
                    completeJournalButton.classList.remove('hidden');
                } else {
                    completeJournalButton.classList.add('hidden');
                }

            } else {
                holdingSummaryCard.classList.add('hidden');
                completeJournalButton.classList.add('hidden'); // Hide if no journal or not active
            }
        } catch (error) {
            console.error('Error fetching portfolio summary:', error);
            holdingSummaryCard.classList.add('hidden');
            completeJournalButton.classList.add('hidden'); // Hide on error
        }
    }

    // --- API & EVENT HANDLERS ---

    // 가격을 퍼센트로 변환
    function calculatePercent(price, currentPrice) {
        if (currentPrice === null || currentPrice === 0) return '';
        const value = parseFloat(price);
        if (isNaN(value)) return '';
        return (((value - currentPrice) / currentPrice) * 100).toFixed(2);
    }

    // 퍼센트를 가격으로 변환
    function calculatePrice(percent, currentPrice) {
        if (currentPrice === null || currentPrice === 0) return '';
        const value = parseFloat(percent);
        if (isNaN(value)) return '';
        return (currentPrice * (1 + (value / 100))).toFixed(2);
    }

    // 목표 가격/퍼센트 입력 핸들러
    function handleTargetInput(event) {
        if (state.currentPrice === null) {
            alert('먼저 주식을 선택하여 현재 가격을 불러와주세요.');
            event.target.value = '';
            return;
        }
        const inputId = event.target.id;
        const value = event.target.value;

        if (inputId === 'target-price') {
            targetPercentInput.value = calculatePercent(value, state.currentPrice);
        } else if (inputId === 'target-percent') {
            targetPriceInput.value = calculatePrice(value, state.currentPrice);
        }
    }

    // 손절 가격/퍼센트 입력 핸들러
    function handleStopInput(event) {
        if (state.currentPrice === null) {
            alert('먼저 주식을 선택하여 현재 가격을 불러와주세요.');
            event.target.value = '';
            return;
        }
        const inputId = event.target.id;
        const value = event.target.value;

        if (inputId === 'stop-price') {
            stopPercentInput.value = calculatePercent(value, state.currentPrice);
        } else if (inputId === 'stop-percent') {
            stopPriceInput.value = calculatePrice(value, state.currentPrice);
        }
    }

    async function selectStock(ticker) {
        searchResultsContainer.innerHTML = '';
        stockSearchInput.value = '';
        try {
            const response = await fetch(`/api/stock/${ticker}/card-details/`);
            if (!response.ok) throw new Error('Failed to fetch stock details.');
            const data = await response.json();
            renderSelectedStockCard(data);
            updateHoldingsDisplay(ticker);
            
            // 주식 선택 시 목표/손절 가격/퍼센트 필드 초기화
            targetPriceInput.value = '';
            targetPercentInput.value = '';
            stopPriceInput.value = '';
            stopPercentInput.value = '';

        } catch (error) {
            console.error('Error selecting stock:', error);
        }
    }

    function renderSearchResults(results) {
        searchResultsContainer.innerHTML = '';
        if (!results.length) return;
        results.forEach(stock => {
            const item = document.createElement('div');
            item.className = 'search-result-item';
            item.textContent = `${stock.name} (${stock.ticker})`;
            item.dataset.ticker = stock.ticker;
            item.addEventListener('click', () => selectStock(stock.ticker));
            searchResultsContainer.appendChild(item);
        });
    }

    const searchStocks = debounce(async (query) => {
        if (query.trim() === '') {
            searchResultsContainer.innerHTML = '';
            return;
        }
        try {
            const response = await fetch(`/api/stock/search/?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            renderSearchResults(data.results);
        } catch (error) {
            console.error('Error searching stocks:', error);
        }
    });

    function updateTradeSide(newSide) {
        state.side = newSide;
        buyButton.classList.toggle('active', newSide === 'BUY');
        sellButton.classList.toggle('active', newSide === 'SELL');
        const sideText = newSide === 'BUY' ? '매수' : '매도';
        tradeInputLabels.forEach(label => {
            label.innerHTML = label.innerHTML.replace(/매수|매도/, sideText);
        });
    }

    async function handleFormSubmit(event) {
        event.preventDefault();
        if (!state.selectedTicker) {
            alert('주식을 선택해주세요.');
            return;
        }
        const payload = {
            ticker_symbol: state.selectedTicker,
            target_price: targetPriceInput.value, // 변경된 값 사용
            stop_price: stopPriceInput.value,     // 변경된 값 사용
            legs: [{
                side: state.side,
                price_per_share: tradePriceInput.value,
                quantity: tradeQuantityInput.value,
                date: tradeDateInput.value,
            }],
            content: tradeReasonInput.value, // '매매이유' 필드 추가
        };

        try {
            const response = await fetch('/api/stock/journals/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify(payload),
            });
            const data = await response.json();
            if (response.ok) {
                alert('매매일지가 성공적으로 작성되었습니다.');
                window.location.href = '/';
            } else {
                alert(`작성 실패: ${data.error || '알 수 없는 오류'}`);
            }
        } catch (error) {
            console.error('Submission error:', error);
            alert('데이터 전송 중 오류가 발생했습니다.');
        }
    }

    // --- INITIALIZATION ---
    stockSearchInput.addEventListener('input', (e) => searchStocks(e.target.value));
    buyButton.addEventListener('click', () => updateTradeSide('BUY'));
    sellButton.addEventListener('click', () => updateTradeSide('SELL'));
    form.addEventListener('submit', handleFormSubmit);

    // 목표/손절 가격/퍼센트 입력 필드에 이벤트 리스너 추가
    targetPriceInput.addEventListener('input', handleTargetInput);
    targetPercentInput.addEventListener('input', handleTargetInput);
    stopPriceInput.addEventListener('input', handleStopInput);
    stopPercentInput.addEventListener('input', handleStopInput);

    // Set initial state
    updateTradeSide('BUY');
    tradeDateInput.valueAsDate = new Date();
});
