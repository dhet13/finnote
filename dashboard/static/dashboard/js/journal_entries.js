// 매매일지 데이터 로드 및 표시 함수들
function loadJournalEntries() {
    console.log('매매일지 데이터 로드 시작');
    
    fetch('/dashboard/api/journal_entries/?limit=10')
        .then(response => response.json())
        .then(data => {
            console.log('매매일지 데이터 로드 완료:', data);
            updateJournalStatistics(data.statistics);
            updateJournalEntriesList(data.recent_entries);
        })
        .catch(error => {
            console.error('매매일지 데이터 로드 실패:', error);
        });
}

function updateJournalStatistics(stats) {
    const statsElement = document.getElementById('journal-stats');
    if (!statsElement) return;
    
    statsElement.innerHTML = `
        <div style="display: flex; gap: 20px; font-size: 14px; color: #536471;">
            <span>총 ${stats.total_entries}개</span>
            <span>주식 ${stats.stock_entries}개</span>
            <span>부동산 ${stats.real_estate_entries}개</span>
            <span>최근 30일 ${stats.recent_entries}개</span>
        </div>
    `;
}

function updateJournalEntriesList(entries) {
    const entriesElement = document.getElementById('journal-entries-list');
    if (!entriesElement) return;
    
    if (entries.length === 0) {
        entriesElement.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #536471; background: #f7f9fa; border-radius: 8px;">
                <p>아직 작성된 매매일지가 없습니다.</p>
                <p style="font-size: 14px; margin-top: 8px;">첫 번째 매매일지를 작성해보세요!</p>
            </div>
        `;
        return;
    }
    
    const entriesHTML = entries.map(entry => `
        <div class="journal-entry-card" style="
            background: white; 
            border: 1px solid #e1e8ed; 
            border-radius: 8px; 
            padding: 16px; 
            margin-bottom: 12px;
            cursor: pointer;
            transition: box-shadow 0.2s ease;
        " onclick="navigateToJournalEntry(${entry.id})">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                <div>
                    <h4 style="margin: 0; font-size: 16px; color: #0f1419;">${entry.asset_name || '알 수 없는 자산'}</h4>
                    <p style="margin: 4px 0 0 0; font-size: 12px; color: #536471;">
                        ${entry.asset_type === 'stock' ? '주식' : entry.asset_type === 'real_estate' ? '부동산' : '기타'}
                    </p>
                </div>
                <div style="text-align: right;">
                    <p style="margin: 0; font-size: 14px; font-weight: 600; color: #0f1419;">
                        ${formatCurrency(entry.total_amount)}
                    </p>
                    <p style="margin: 4px 0 0 0; font-size: 12px; color: #536471;">
                        ${new Date(entry.trade_date || entry.created_at).toLocaleDateString('ko-KR')}
                    </p>
                </div>
            </div>
            <p style="margin: 0; font-size: 14px; color: #0f1419; line-height: 1.4; 
               display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                ${entry.content || '내용 없음'}
            </p>
        </div>
    `).join('');
    
    entriesElement.innerHTML = entriesHTML;
}

function navigateToJournalEntry(entryId) {
    console.log('매매일지 상세 페이지로 이동:', entryId);
    window.location.href = `/journals/post/${entryId}/`;
}

// 포트폴리오 페이지 초기화에 매매일지 로드 추가
function initializePortfolioPageWithJournal() {
    console.log('포트폴리오 페이지 초기화 (매매일지 포함)');
    
    // 기존 포트폴리오 초기화
    if (typeof initializePortfolioPage === 'function') {
        initializePortfolioPage();
    }
    
    // 매매일지 데이터 로드
    loadJournalEntries();
}

// 전역 함수로 등록
window.loadJournalEntries = loadJournalEntries;
window.updateJournalStatistics = updateJournalStatistics;
window.updateJournalEntriesList = updateJournalEntriesList;
window.navigateToJournalEntry = navigateToJournalEntry;
window.initializePortfolioPageWithJournal = initializePortfolioPageWithJournal;

