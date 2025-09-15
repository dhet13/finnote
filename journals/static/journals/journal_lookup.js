
console.log("✅ journal_lookup.js loaded and running!");

document.addEventListener('DOMContentLoaded', function () {

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

    const targetPriceInput = document.getElementById('target-price');
    const targetPercentInput = document.getElementById('target-percent');
    const stopPriceInput = document.getElementById('stop-price');
    const stopPercentInput = document.getElementById('stop-percent');

    const tradeReasonInput = document.getElementById('trade-reason');
    const completeJournalButton = document.getElementById('complete-journal-btn');

    // --- RENDER FUNCTIONS ---

    let stockChart = null; 

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
                        pointRadius: 0,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } },
                    scales: { x: { display: false }, y: { display: false } }
                }
            });

        } catch (error) {
            console.error('Error fetching or rendering stock history:', error);
        }
    }

    function renderSelectedStockCard(data) {
        state.selectedTicker = data.ticker;
        state.currentPrice = parseFloat(data.price);

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

                if (parseFloat(data.net_quantity) === 0 && data.status === 'completed') {
                    completeJournalButton.classList.remove('hidden');
                } else {
                    completeJournalButton.classList.add('hidden');
                }

            } else {
                holdingSummaryCard.classList.add('hidden');
                completeJournalButton.classList.add('hidden');
            }
        } catch (error) {
            console.error('Error fetching portfolio summary:', error);
            holdingSummaryCard.classList.add('hidden');
            completeJournalButton.classList.add('hidden');
        }
    }

    // --- API & EVENT HANDLERS ---

    function calculatePercent(price, currentPrice) {
        if (currentPrice === null || currentPrice === 0) return '';
        const value = parseFloat(price);
        if (isNaN(value)) return '';
        return (((value - currentPrice) / currentPrice) * 100).toFixed(2);
    }

    function calculatePrice(percent, currentPrice) {
        if (currentPrice === null || currentPrice === 0) return '';
        const value = parseFloat(percent);
        if (isNaN(value)) return '';
        return (currentPrice * (1 + (value / 100))).toFixed(2);
    }

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
        stockSearchInput.value = ticker;
        try {
            const response = await fetch(`/api/stock/${ticker}/card-details/`);
            if (!response.ok) {
                selectedStockCardContainer.innerHTML = `<p style="color:red;">종목 정보를 찾을 수 없습니다. 정확한 Ticker를 입력해주세요 (예: 005930.KS)</p>`;
                selectedStockCardContainer.classList.remove('hidden');
                throw new Error('Failed to fetch stock details.');
            }
            const data = await response.json();
            renderSelectedStockCard(data);
            updateHoldingsDisplay(ticker);
            
            targetPriceInput.value = '';
            targetPercentInput.value = '';
            stopPriceInput.value = '';
            stopPercentInput.value = '';

        } catch (error) {
            console.error('Error selecting stock:', error);
        }
    }

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
            target_price: targetPriceInput.value,
            stop_price: stopPriceInput.value,
            legs: [{
                side: state.side,
                price_per_share: tradePriceInput.value,
                quantity: tradeQuantityInput.value,
                date: tradeDateInput.value,
            }],
            content: tradeReasonInput.value,
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
    const searchIcon = document.getElementById('journal-search-icon');

    function handleLookup() {
        const ticker = stockSearchInput.value.trim().toUpperCase();
        if (ticker) {
            selectStock(ticker);
        }
    }

    stockSearchInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') {
            handleLookup();
        }
    });

    searchIcon.addEventListener('click', handleLookup);

    buyButton.addEventListener('click', () => updateTradeSide('BUY'));
    sellButton.addEventListener('click', () => updateTradeSide('SELL'));
    form.addEventListener('submit', handleFormSubmit);

    targetPriceInput.addEventListener('input', handleTargetInput);
    targetPercentInput.addEventListener('input', handleTargetInput);
    stopPriceInput.addEventListener('input', handleStopInput);
    stopPercentInput.addEventListener('input', handleStopInput);

    updateTradeSide('BUY');
    tradeDateInput.valueAsDate = new Date();
});
