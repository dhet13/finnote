// Simple debounce
// Simple debounce
const jcDebounce = (fn, wait = 400) => {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), wait); };
};

(function () {
  const root = document.getElementById('journal-compose');
  if (!root) return;

  const search = document.getElementById('jc-search'); // Still needed for keyup listener in _compose_form.html
  const selected = document.getElementById('jc-selected'); // Still needed for stock card display
  const logo = document.getElementById('jc-logo'); // Still needed for stock card display
  const tickerEl = document.getElementById('jc-ticker'); // Still needed for stock card display
  const priceEl = document.getElementById('jc-price'); // Still needed for stock card display
  const changeEl = document.getElementById('jc-change'); // Still needed for stock card display
  const spark = document.getElementById('jc-spark'); // Still needed for stock card display

  const tPrice = document.getElementById('jc-target-price');
  const tPct = document.getElementById('jc-target-pct');
  const sPrice = document.getElementById('jc-stop-price');
  const sPct = document.getElementById('jc-stop-pct');

  const sideBuy = document.getElementById('jc-side-buy');
  const sideSell = document.getElementById('jc-side-sell');

  const hWrap = document.getElementById('jc-holdings');
  const hShares = document.getElementById('jc-holdings-shares');
  const pnlRate = document.getElementById('jc-pnl-rate');
  const avgSell = document.getElementById('jc-avg-sell');

  const tradePrice = document.getElementById('jc-trade-price');
  const tradeQty = document.getElementById('jc-trade-qty');
  const tradeDate = document.getElementById('jc-trade-date');
  const closeTradeContainer = document.getElementById('jc-close-trade-container'); // New: reference to the container
  const closeTradeCheckbox = document.getElementById('jc-close-trade'); // New: reference to the checkbox
  const reason = document.getElementById('jc-reason');

  const fTitle = document.getElementById('f-title');
  const fContent = document.getElementById('f-content');
  const fTicker = document.getElementById('f-ticker');
  const fTarget = document.getElementById('f-target');
  const fStop = document.getElementById('f-stop');

  let state = {
    ticker: '',
    price: 0,
    prevClose: 0,
    changePct: 0,
    side: 'SELL',
    journalId: null, // New: to store the current journal ID
  };

  // Removed old renderSparkline as it's now in _stock_card.html
  // Removed old fetchQuote as it's now handled by fetchAndRenderStockCard

  // New: Function to update holdings display and close trade visibility
  function updateHoldingsDisplay(netQty, pnl, status) {
    if (netQty !== null) {
      hShares.textContent = netQty.toLocaleString();
      hWrap.style.display = 'flex'; // Show holdings card if netQty is available
    } else {
      hShares.textContent = '0';
      hWrap.style.display = 'none'; // Hide if no netQty
    }

    if (pnl !== null) {
      pnlRate.textContent = `${pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}%`;
      pnlRate.style.color = pnl >= 0 ? '#22c55e' : '#ef4444';
    } else {
      pnlRate.textContent = '+0.00%';
      pnlRate.style.color = 'inherit';
    }

    // avgSell is not returned by add_stock_trade_api, so it needs to be recomputed or fetched
    // For now, we'll leave it as is or update based on local calculation if possible.
    // The wireframe shows avgSell, but the backend only calculates avg_sell_price on the journal.
    // For simplicity, we'll just update the shares and pnl.

    // Show/hide "매매 종료" container
    if (status === 'completed') {
      closeTradeContainer.style.display = 'flex';
      closeTradeCheckbox.checked = true; // Mark as checked if completed
      closeTradeCheckbox.disabled = true; // Disable if completed
    } else {
      closeTradeContainer.style.display = 'none';
      closeTradeCheckbox.checked = false;
      closeTradeCheckbox.disabled = false;
    }
  }

  // New: Function to update trade form labels based on side
  function updateTradeFormUI(side) {
    const priceLabel = document.querySelector('label[for="jc-trade-price"]');
    const qtyLabel = document.querySelector('label[for="jc-trade-qty"]');
    const dateLabel = document.querySelector('label[for="jc-trade-date"]');

    if (side === 'BUY') {
      priceLabel.textContent = '매수 금액(원)';
      qtyLabel.textContent = '매수 수량';
      dateLabel.textContent = '매수 날짜';
    } else { // SELL
      priceLabel.textContent = '매도 금액(원)';
      qtyLabel.textContent = '매도 수량';
      dateLabel.textContent = '매도 날짜';
    }
  }

  // Recompute targets and update hidden fields
  function recomputeTargets() {
    // price <-> pct sync for both target/stop
    const p = state.price || 0;
    const sync = (priceEl, pctEl) => {
      const pf = parseFloat(priceEl.value);
      const cf = parseFloat(pctEl.value);
      if (document.activeElement === priceEl && p) {
        pctEl.value = (((pf - p) / p) * 100).toFixed(2);
      } else if (document.activeElement === pctEl && p) {
        priceEl.value = (p * (1 + (cf/100))).toFixed(2);
      }
    };
    sync(tPrice, tPct);
    sync(sPrice, sPct);

    // holdings preview based on entered qty/price (this is now handled by updateHoldingsDisplay from backend)
    // map to hidden fields
    fTicker.value = state.ticker || '';
    fTarget.value = tPrice.value || '';
    fStop.value = sPrice.value || '';
    fTitle.value = state.ticker ? `${state.ticker} 매매일지` : '매매일지';
    fContent.value = reason.value || '';
  }

  function markSide(side) {
    state.side = side;
    if (side === 'BUY') {
      sideBuy.style.background = '#22c55e';
      sideBuy.style.color = 'white';
      sideSell.style.background = 'white';
      sideSell.style.color = 'inherit';
      sideSell.style.border = '1px solid var(--border-color)';
    } else { // SELL
      sideSell.style.background = '#22c55e';
      sideSell.style.color = 'white';
      sideBuy.style.background = 'white';
      sideBuy.style.color = 'inherit';
      sideBuy.style.border = '1px solid var(--border-color)';
    }
    updateTradeFormUI(side); // Call new function
  }

  // inc/dec handlers
  function stepInput(id, delta) {
    const el = document.getElementById(id);
    if (!el) return;
    const v = parseFloat(el.value || '0') + delta;
    el.value = (Math.max(v, 0)).toFixed(el.step && el.step.includes('.') ? 2 : 0);
    recomputeTargets();
  }

  // Bindings
  // Removed search.addEventListener('input', onSearch); as it's handled by _compose_form.html
  [tPrice, tPct, sPrice, sPct, tradePrice, tradeQty, reason].forEach(el => {
    if (!el) return;
    el.addEventListener('input', recomputeTargets);
  });
  sideBuy.addEventListener('click', () => markSide('BUY'));
  sideSell.addEventListener('click', () => markSide('SELL'));
  markSide('SELL'); // Initial state

  document.querySelectorAll('.jc-inc').forEach(b => {
    b.addEventListener('click', () => stepInput(b.dataset.target, (b.dataset.target === 'jc-trade-qty') ? 1 : 10));
  });
  document.querySelectorAll('.jc-dec').forEach(b => {
    b.addEventListener('click', () => stepInput(b.dataset.target, (b.dataset.target === 'jc-trade-qty') ? -1 : -10));
  });

  // Expose updateHoldingsDisplay globally for _compose_form.html to call after trade submission
  window.updateHoldingsDisplay = updateHoldingsDisplay;
  window.state = state; // Expose state for debugging or other modules if needed

})();

(function () {
  const root = document.getElementById('journal-compose');
  if (!root) return;

  const search = document.getElementById('jc-search');
  const selected = document.getElementById('jc-selected');
  const logo = document.getElementById('jc-logo');
  const tickerEl = document.getElementById('jc-ticker');
  const priceEl = document.getElementById('jc-price');
  const changeEl = document.getElementById('jc-change');
  const spark = document.getElementById('jc-spark');

  const tPrice = document.getElementById('jc-target-price');
  const tPct = document.getElementById('jc-target-pct');
  const sPrice = document.getElementById('jc-stop-price');
  const sPct = document.getElementById('jc-stop-pct');

  const sideBuy = document.getElementById('jc-side-buy');
  const sideSell = document.getElementById('jc-side-sell');

  const hWrap = document.getElementById('jc-holdings');
  const hShares = document.getElementById('jc-holdings-shares');
  const pnlRate = document.getElementById('jc-pnl-rate');
  const avgSell = document.getElementById('jc-avg-sell');

  const tradePrice = document.getElementById('jc-trade-price');
  const tradeQty = document.getElementById('jc-trade-qty');
  const tradeDate = document.getElementById('jc-trade-date');
  const closeTrade = document.getElementById('jc-close-trade');
  const reason = document.getElementById('jc-reason');

  const fTitle = document.getElementById('f-title');
  const fContent = document.getElementById('f-content');
  const fTicker = document.getElementById('f-ticker');
  const fTarget = document.getElementById('f-target');
  const fStop = document.getElementById('f-stop');

  let state = {
    ticker: '',
    price: 0,
    prevClose: 0,
    changePct: 0,
    side: 'SELL',
  };

  function renderSparkline(values = []) {
    if (!spark) return;
    const ctx = spark.getContext('2d');
    const w = spark.width, h = spark.height;
    ctx.clearRect(0,0,w,h);
    if (!values.length) return;
    const min = Math.min(...values), max = Math.max(...values);
    const pad = 2;
    ctx.strokeStyle = '#22c55e';
    ctx.lineWidth = 2;
    ctx.beginPath();
    values.forEach((v, i) => {
      const x = pad + (i * (w - pad*2) / (values.length - 1 || 1));
      const y = h - pad - ((v - min) / (max - min || 1)) * (h - pad*2);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  async function fetchQuote(sym) {
    try {
      const res = await fetch(`/api/stock/quote/?ticker=${encodeURIComponent(sym)}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'quote failed');
      return data;
    } catch (e) {
      console.error(e);
      return null;
    }
  }

  const onSearch = jcDebounce(async (e) => {
    const v = e.target.value.trim();
    if (!v) return;
    const q = await fetchQuote(v);
    if (!q) return;
    state.ticker = q.ticker;
    state.price = parseFloat(q.price);
    state.prevClose = parseFloat(q.prev_close);
    state.changePct = parseFloat(q.change_percent);

    selected.style.display = 'flex';
    logo.textContent = (state.ticker || '?').slice(0,1);
    tickerEl.textContent = state.ticker;
    priceEl.textContent = q.price;
    changeEl.textContent = `${state.changePct >= 0 ? '+' : ''}${q.change_percent}%`;
    changeEl.style.color = state.changePct >= 0 ? '#22c55e' : '#ef4444';
    renderSparkline([
      state.prevClose * 0.98,
      state.prevClose,
      (state.prevClose + state.price)/2,
      state.price
    ]);
    recomputeTargets();
  });

  function recomputeTargets() {
    // price <-> pct sync for both target/stop
    const p = state.price || 0;
    const sync = (priceEl, pctEl) => {
      const pf = parseFloat(priceEl.value);
      const cf = parseFloat(pctEl.value);
      if (document.activeElement === priceEl && p) {
        pctEl.value = (((pf - p) / p) * 100).toFixed(2);
      } else if (document.activeElement === pctEl && p) {
        priceEl.value = (p * (1 + (cf/100))).toFixed(2);
      }
    };
    sync(tPrice, tPct);
    sync(sPrice, sPct);

    // holdings preview based on entered qty/price
    const qty = parseFloat(tradeQty.value) || 0;
    const px = parseFloat(tradePrice.value) || state.price;
    if (qty > 0) {
      hWrap.style.display = 'flex';
      hShares.textContent = qty.toLocaleString();
      const pnl = (state.price - px) / (px || 1) * 100;
      pnlRate.textContent = `${pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}%`;
      pnlRate.style.color = pnl >= 0 ? '#22c55e' : '#ef4444';
      avgSell.textContent = `$${px.toFixed(2)}`;
    } else {
      hWrap.style.display = 'none';
    }

    // map to hidden fields
    fTicker.value = state.ticker || '';
    fTarget.value = tPrice.value || '';
    fStop.value = sPrice.value || '';
    fTitle.value = state.ticker ? `${state.ticker} 매매일지` : '매매일지';
    fContent.value = reason.value || '';
  }

  function markSide(side) {
    state.side = side;
    if (side === 'BUY') {
      sideBuy.style.background = '#22c55e';
      sideBuy.style.color = 'white';
      sideSell.style.background = 'white';
      sideSell.style.color = 'inherit';
      sideSell.style.border = '1px solid var(--border-color)';
    } else {
      sideSell.style.background = '#22c55e';
      sideSell.style.color = 'white';
      sideBuy.style.background = 'white';
      sideBuy.style.color = 'inherit';
      sideBuy.style.border = '1px solid var(--border-color)';
    }
  }

  // inc/dec handlers
  function stepInput(id, delta) {
    const el = document.getElementById(id);
    if (!el) return;
    const v = parseFloat(el.value || '0') + delta;
    el.value = (Math.max(v, 0)).toFixed(el.step && el.step.includes('.') ? 2 : 0);
    recomputeTargets();
  }

  // Bindings
  if (search) search.addEventListener('input', onSearch);
  [tPrice, tPct, sPrice, sPct, tradePrice, tradeQty, reason].forEach(el => {
    if (!el) return;
    el.addEventListener('input', recomputeTargets);
  });
  sideBuy.addEventListener('click', () => markSide('BUY'));
  sideSell.addEventListener('click', () => markSide('SELL'));
  markSide('SELL');

  document.querySelectorAll('.jc-inc').forEach(b => {
    b.addEventListener('click', () => stepInput(b.dataset.target, (b.dataset.target === 'jc-trade-qty') ? 1 : 10));
  });
  document.querySelectorAll('.jc-dec').forEach(b => {
    b.addEventListener('click', () => stepInput(b.dataset.target, (b.dataset.target === 'jc-trade-qty') ? -1 : -10));
  });
})();

