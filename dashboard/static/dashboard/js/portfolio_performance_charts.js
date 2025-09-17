(function () {
    const API_ENDPOINT = '/dashboard/api/portfolio/';
    const TOTAL_API_ENDPOINT = '/dashboard/api/total/?interval=weekly';

    const defaultState = {
        interval: 'weekly',
        sectorReturnPeriod: 'daily',
        data: null,
    };

    const state = Object.assign({}, defaultState, window.__portfolioState__ || {});
    window.__portfolioState__ = state;

    const charts = window.__portfolioCharts__ || {};
    window.__portfolioCharts__ = charts;

    const sectorColors = {
        Technology: '#4f46e5',
        '기술주': '#4f46e5',
        Financials: '#059669',
        '금융주': '#059669',
        Consumer: '#dc2626',
        '소비재': '#dc2626',
        Healthcare: '#f59e0b',
        '헬스케어': '#f59e0b',
        Energy: '#8b5cf6',
        '에너지': '#8b5cf6',
        Industrials: '#06b6d4',
        '산업재': '#06b6d4',
        Other: '#6b7280',
        '기타': '#6b7280',
    };

    function formatCurrency(value) {
        if (!isFinite(value)) return '-';
        return `${Math.round(value).toLocaleString()}원`;
    }

    function formatPercent(value, fraction = 2) {
        if (!isFinite(value)) return '0.00%';
        const formatted = value.toFixed(fraction);
        return `${value > 0 ? '+' : ''}${formatted}%`;
    }

    function destroyChart(key) {
        if (charts[key] && typeof charts[key].destroy === 'function') {
            charts[key].destroy();
            delete charts[key];
        }
    }

    function showEmptyPortfolioState(selector) {
        const container = selector ? document.querySelector(selector) : document.querySelector('.portfolio-main-content');
        if (!container) return;
        container.innerHTML = '<div class="no-data-message">표시할 데이터가 없습니다.</div>';
    }

    function showPortfolioLoginRequired() {
        const host = document.querySelector('.portfolio-main-content');
        if (!host) return;
        host.innerHTML = `
            <div class="login-required-message">
                <h4>로그인이 필요합니다</h4>
                <p>포트폴리오 정보를 보려면 로그인하세요.</p>
                <a href="/accounts/login/" class="btn">로그인</a>
            </div>
        `;
    }

    async function initializePortfolioPageWithAuth() {
        try {
            const response = await fetch(TOTAL_API_ENDPOINT, { credentials: 'same-origin' });
            if (response.status === 401) {
                showPortfolioLoginRequired();
                return false;
            }
            await initializePortfolioPage();
            return true;
        } catch (error) {
            console.error('포트폴리오 페이지 로그인 상태 확인 실패:', error);
            showPortfolioLoginRequired();
            return false;
        }
    }

    async function initializePortfolioPage() {
        initializeAssetTypeButtons();
        initializeStockPeriodButtons();
        initializePropertyPeriodButtons();
        initializeSectorReturnButtons();
        initializePropertyReturnButtons();
        await loadPortfolioData(state.interval);
    }

    function initializeAssetTypeButtons() {
        const buttons = document.querySelectorAll('.asset-type-btn');
        buttons.forEach(button => {
            button.addEventListener('click', () => {
                buttons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                const type = button.dataset.type;
                if (type === 'stock') {
                    showStockPortfolio();
                } else if (type === 'real_estate') {
                    showPropertyPortfolio();
                }
            });
        });
    }

    function initializeStockPeriodButtons() {
        const buttons = document.querySelectorAll('.stock-period-btn');
        buttons.forEach(button => {
            button.addEventListener('click', () => {
                buttons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                updateStockPerformanceChart(button.dataset.period || '1M');
            });
        });
    }

    function initializePropertyPeriodButtons() {
        const buttons = document.querySelectorAll('.property-period-btn');
        buttons.forEach(button => {
            button.addEventListener('click', () => {
                buttons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
            });
        });
    }

    function initializeSectorReturnButtons() {
        const buttons = document.querySelectorAll('.sector-return-btn');
        buttons.forEach(button => {
            button.addEventListener('click', () => {
                buttons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                state.sectorReturnPeriod = button.dataset.period || 'daily';
                if (state.data) renderSectorCards(state.data.stock_holdings || []);
            });
        });
    }

    function initializePropertyReturnButtons() {
        const buttons = document.querySelectorAll('.property-return-btn');
        buttons.forEach(button => {
            button.addEventListener('click', () => {
                buttons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
            });
        });
    }

    function showStockPortfolio() {
        const stock = document.getElementById('stockPortfolio');
        const property = document.getElementById('propertyPortfolio');
        if (stock) stock.style.display = 'block';
        if (property) property.style.display = 'none';
    }

    function showPropertyPortfolio() {
        const stock = document.getElementById('stockPortfolio');
        const property = document.getElementById('propertyPortfolio');
        if (stock) stock.style.display = 'none';
        if (property) property.style.display = 'block';
    }

    async function loadPortfolioData(interval = 'weekly') {
        try {
            state.interval = interval;
            const response = await fetch(`${API_ENDPOINT}?interval=${interval}`, { credentials: 'same-origin' });
            if (response.status === 401) {
                showPortfolioLoginRequired();
                return;
            }
            if (!response.ok) throw new Error(`API 호출 실패: ${response.status}`);
            const data = await response.json();
            state.data = data;
            renderPortfolio(data);
        } catch (error) {
            console.error('포트폴리오 데이터 로드 오류:', error);
            showPortfolioLoginRequired();
        }
    }

    function renderPortfolio(data) {
        renderStockPerformanceChart(data.timeseries_data || []);
        renderSectorPieChart(data.sector_breakdown || {});
        renderSectorCards(data.stock_holdings || []);
        renderPropertyCards(data.real_estate_holdings || []);
    }

    function renderStockPerformanceChart(timeseries) {
        const ctx = document.getElementById('stockPerformanceChart');
        if (!ctx) return;

        const labels = timeseries.map(item => {
            const date = item.date ? new Date(item.date) : null;
            if (!date || Number.isNaN(date.getTime())) return '';
            return `${date.getMonth() + 1}/${date.getDate()}`;
        });

        const values = timeseries.map(item => Number(item.market_value_krw ?? item.market_value ?? 0));

        destroyChart('stockPerformance');
        if (!values.some(v => v > 0)) {
            ctx.getContext('2d').clearRect(0, 0, ctx.width, ctx.height);
            return;
        }

        charts.stockPerformance = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: '포트폴리오 평가액',
                        data: values,
                        borderColor: '#4f46e5',
                        backgroundColor: 'rgba(79, 70, 229, 0.1)',
                        tension: 0.25,
                        fill: true,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        ticks: {
                            callback: value => `${Math.round(value).toLocaleString()}원`,
                        },
                    },
                },
            },
        });
    }

    function updateStockPerformanceChart(period) {
        if (!state.data) return;
        renderStockPerformanceChart(state.data.timeseries_data || []);
    }

    function renderSectorPieChart(breakdown) {
        const canvas = document.getElementById('stockSectorPieChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const labels = Object.keys(breakdown);
        const values = labels.map(label => Number(breakdown[label]));

        destroyChart('sectorPie');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (!labels.length || !values.some(v => v > 0)) {
            renderSectorLegend([]);
            return;
        }

        const colors = labels.map(label => sectorColors[label] || randomColor());

        charts.sectorPie = new Chart(ctx, {
            type: 'pie',
            data: {
                labels,
                datasets: [
                    {
                        data: values,
                        backgroundColor: colors,
                        borderColor: '#ffffff',
                        borderWidth: 2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: context => {
                                const dataset = context.dataset.data;
                                const total = dataset.reduce((sum, value) => sum + value, 0);
                                const value = context.parsed || 0;
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';
                                return `${context.label}: ${percentage}% (${Math.round(value).toLocaleString()}원)`;
                            },
                        },
                    },
                    datalabels: typeof ChartDataLabels !== 'undefined'
                        ? {
                              color: '#ffffff',
                              font: { weight: 'bold', size: 12 },
                              formatter: (value, context) => {
                                  const total = context.dataset.data.reduce((sum, item) => sum + item, 0);
                                  const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';
                                  return `${context.chart.data.labels[context.dataIndex]}\n${percentage}%`;
                              },
                          }
                        : undefined,
                },
            },
        });

        renderSectorLegend(labels.map((label, index) => ({
            label,
            value: values[index],
            color: colors[index],
        })));
    }

    function renderSectorLegend(entries) {
        const canvas = document.getElementById('stockSectorPieChart');
        if (!canvas) return;
        const container = canvas.parentElement;
        if (!container) return;

        let legend = container.querySelector('.sector-pie-legend');
        if (!legend) {
            legend = document.createElement('div');
            legend.className = 'sector-pie-legend';
            container.appendChild(legend);
        }

        legend.innerHTML = '';
        if (!entries.length) {
            legend.innerHTML = '<div class="sector-legend-item" style="color:#6b7280;">섹터 데이터가 없습니다.</div>';
            return;
        }

        const total = entries.reduce((sum, item) => sum + item.value, 0);
        legend.innerHTML = entries
            .map(({ label, value, color }) => {
                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';
                return `
                    <div class="sector-legend-item" style="display:flex; justify-content:space-between; align-items:center; font-size:13px; color:#0f1419; gap:12px;">
                        <span style="display:flex; align-items:center; gap:8px;">
                            <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:${color};"></span>
                            ${label}
                        </span>
                        <span style="font-weight:600;">${percentage}%</span>
                    </div>`;
            })
            .join('');
    }

    function renderSectorCards(stockHoldings) {
        const container = document.querySelector('.sector-cards-grid');
        if (!container) return;

        container.innerHTML = '';
        if (!Array.isArray(stockHoldings) || !stockHoldings.length) {
            showEmptyPortfolioState('.sector-cards-grid');
            return;
        }

        const groups = stockHoldings.reduce((acc, holding) => {
            const sector = holding.sector || holding.sector_name || 'Other';
            if (!acc[sector]) acc[sector] = [];
            acc[sector].push(holding);
            return acc;
        }, {});

        Object.entries(groups).forEach(([sector, holdings]) => {
            const sectorColor = sectorColors[sector] || randomColor();
            const totalValueKRW = holdings.reduce((sum, holding) => sum + Number(holding.market_value_krw ?? holding.market_value ?? 0), 0);

            const cardsMarkup = holdings
                .map(holding => {
                    const marketValueKRW = Number(holding.market_value_krw ?? holding.market_value ?? 0);
                    const investedAmountKRW = Number(holding.invested_amount_krw ?? holding.invested_amount ?? 0);
                    const quantity = Number(holding.quantity ?? holding.total_quantity ?? 0);
                    const avgBuyPriceKRW = Number(holding.avg_buy_price_krw ?? (quantity > 0 && investedAmountKRW ? investedAmountKRW / quantity : 0));
                    const pnlPercent = Number(holding.pnl_percentage ?? holding.return_rate ?? 0);

                    const weight = totalValueKRW > 0 ? `${((marketValueKRW / totalValueKRW) * 100).toFixed(1)}%` : '0%';
                    const returnClass = pnlPercent > 0 ? 'positive' : (pnlPercent < 0 ? 'negative' : 'neutral');
                    const country = (holding.country || holding.currency || 'KR').toUpperCase();
                    const flag = country === 'US' ? '🇺🇸' : (country === 'JP' ? '🇯🇵' : '🇰🇷');
                    const marketBadge = `${flag} ${country}`.trim();
                    const name = holding.name || holding.asset_name || holding.stock_name || 'Unknown';
                    const ticker = holding.ticker || holding.symbol || holding.stock_ticker_symbol || '';

                    return `
                        <div class="portfolio-item stock-item clickable" data-ticker="${ticker}" data-stock="${encodeURIComponent(name)}">
                            <div class="portfolio-item-name">
                                <span class="portfolio-item-market">${marketBadge}</span>
                                <span class="portfolio-item-title">${name}</span>
                            </div>
                            <div class="portfolio-item-details">
                                <span>보유량 ${quantity ? `${quantity.toLocaleString()}주` : '-'}</span>
                                <span>평균매수가 ${avgBuyPriceKRW > 0 ? formatCurrency(avgBuyPriceKRW) : '-'}</span>
                                <span>총매수금액 ${investedAmountKRW > 0 ? formatCurrency(investedAmountKRW) : '-'}</span>
                            </div>
                            <div class="portfolio-item-right">
                                <div class="portfolio-item-weight">${weight}</div>
                                <div class="portfolio-item-value">${formatCurrency(marketValueKRW)}</div>
                                <div class="portfolio-item-return ${returnClass}">${formatPercent(pnlPercent)}</div>
                            </div>
                        </div>`;
                })
                .join('');

            const card = document.createElement('div');
            card.className = 'sector-card';
            card.innerHTML = `
                <div class="sector-header">
                    <h4><span class="sector-indicator" style="background:${sectorColor};"></span>${sector}</h4>
                    <span class="sector-value">${formatCurrency(totalValueKRW)}</span>
                </div>
                <div class="sector-holdings">${cardsMarkup}</div>`;

            container.appendChild(card);
        });

        addStockCardClickListeners();
    }

    function addStockCardClickListeners() {
        document.querySelectorAll('.stock-item.clickable').forEach(card => {
            card.addEventListener('click', () => {
                const ticker = card.dataset.ticker;
                if (ticker) {
                    window.location.href = `/journals/stock/summary/${ticker}/`;
                }
            });
        });
    }

    function renderPropertyCards(propertyHoldings) {
        const container = document.querySelector('.property-cards-grid');
        if (!container) return;

        container.innerHTML = '';
        if (!Array.isArray(propertyHoldings) || !propertyHoldings.length) {
            showEmptyPortfolioState('.property-cards-grid');
            return;
        }

        propertyHoldings.forEach(holding => {
            const card = document.createElement('div');
            card.className = 'property-card';
            card.innerHTML = `
                <div class="property-header">
                    <h4>${holding.name || '자산'}</h4>
                    <span class="property-value">${formatCurrency(holding.market_value ?? holding.market_value_krw ?? 0)}</span>
                </div>
                <div class="property-details">
                    <div class="property-detail">
                        <span class="detail-label">지역</span>
                        <span class="detail-value">${holding.region || holding.sector_or_region || '기타'}</span>
                    </div>
                    <div class="property-detail">
                        <span class="detail-label">보유</span>
                        <span class="detail-value">${Number(holding.quantity ?? 0).toLocaleString()}</span>
                    </div>
                </div>`;
            container.appendChild(card);
        });
    }

    function randomColor() {
        const palette = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'];
        return palette[Math.floor(Math.random() * palette.length)];
    }

    window.initializePortfolioPageWithAuth = initializePortfolioPageWithAuth;
    window.initializePortfolioPage = initializePortfolioPage;
    window.initializeAssetTypeButtons = initializeAssetTypeButtons;
    window.initializeStockPeriodButtons = initializeStockPeriodButtons;
    window.initializePropertyPeriodButtons = initializePropertyPeriodButtons;
    window.initializeSectorReturnButtons = initializeSectorReturnButtons;
    window.initializePropertyReturnButtons = initializePropertyReturnButtons;
    window.initializeStockPortfolio = () => loadPortfolioData(state.interval);
    window.initializeRealEstatePortfolio = () => loadPortfolioData(state.interval);
    window.initializeStockPerformanceChart = () => renderStockPerformanceChart(state.data ? state.data.timeseries_data : []);
    window.initializePropertyPerformanceChart = () => {};
    window.loadPortfolioData = loadPortfolioData;
    window.showPortfolioLoginRequired = showPortfolioLoginRequired;
    window.showEmptyPortfolioState = showEmptyPortfolioState;
    window.showStockPortfolio = showStockPortfolio;
    window.showPropertyPortfolio = showPropertyPortfolio;
})();
