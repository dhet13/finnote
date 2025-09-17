from dashboard.views.services import DashboardDataCalculator
from accounts.models import User

user_id = 1
calculator = DashboardDataCalculator(user_id=user_id, asset_type=None, interval='weekly')

try:
    entries = calculator.get_recent_journal_entries(10)
    print('get_recent_journal_entries 성공:', len(entries), '개 항목')
    print('첫 번째 항목:', entries[0] if entries else 'None')
except Exception as e:
    print('get_recent_journal_entries 오류:', str(e))
    import traceback
    traceback.print_exc()

